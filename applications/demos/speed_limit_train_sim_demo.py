# %%
import altrios as alt
import time
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd
sns.set()

# %%


# train_sim = alt.SpeedLimitTrainSim.valid()
rail_vehicle_file = "rolling_stock/rail_vehicles.csv"
rail_vehicle_map = alt.import_rail_vehicles(
    str(alt.resources_root() / rail_vehicle_file)
)
location_map = alt.import_locations(
    str(alt.resources_root() / "networks/default_locations.csv")
)

train_summary = alt.TrainSummary(
    list(rail_vehicle_map.keys())[1],
    0,
    100,
    None,  # defaults to freight
    None,
    None,
)


# %% load timed pathes file generated by sim manager demo
train_idx = 1
df_timed_paths = df_timed_paths[df_timed_paths['Train ID'] == train_idx]
df_timed_paths = df_timed_paths.iloc[0:-1, :]
train_path = []
for id, row in df_timed_paths.iterrows():
    train_path.append(alt.LinkIdx(int(row.link_idx)))

# %%
save_interval = 100


def get_train_sim(
        loco_con: alt.Consist = alt.Consist.default()
    ) -> alt.SpeedLimitTrainSim:
    # function body
    tsb = alt.TrainSimBuilder(
        "demo_train",
        "Hibbing",
        "Allouez",
        train_summary,
        loco_con,
    )
    train_sim = tsb.make_speed_limit_train_sim(
        rail_vehicle_map,
        location_map,
        save_interval=save_interval,
    )
    network_filename_path = alt.resources_root() / "networks/Taconite.yaml"
    train_sim.extend_path(
        str(network_filename_path),
        train_path
    )

    train_sim.set_save_interval(save_interval)
    return train_sim


# %%
train_sim = get_train_sim()

t0 = time.perf_counter()
train_sim.walk()
t1 = time.perf_counter()
print(f'Time to simulate: {t1 - t0:.5g}')

# %%

fig, ax = plt.subplots(3, 1, sharex=True)
start_idx = 0
end_idx = -1

ax[0].plot(
    np.array(train_sim.history.time_seconds)[start_idx:end_idx],
    np.array(train_sim.history.pwr_whl_out_watts)[start_idx:end_idx],
    label="whl_out",
)
# ax[0].plot(
#     np.array(train_sim.history.time_seconds)[start_idx:end_idx],
#     (np.array(train_sim.fric_brake.history.force_newtons) *
#         np.array(train_sim.history.velocity_meters_per_second))[start_idx:end_idx],
#     label="fric brake",
# )
ax[0].set_ylabel('Power [W]')
ax[0].legend(loc="lower right")

# ax[1].plot(
#     np.array(train_sim.history.time_seconds)[start_idx:end_idx],
#     np.array(train_sim.fric_brake.history.force_newtons)[
#         start_idx:end_idx],
# )
# ax[1].set_ylabel('Brake Force [N]')

ax[1].plot(
    np.array(train_sim.history.time_seconds)[start_idx:end_idx],
    np.array(train_sim.loco_con.loco_vec.tolist()[1].res.history.soc)[
        start_idx:end_idx],
)
ax[1].set_ylabel('BEL SOC')

ax[-1].plot(
    np.array(train_sim.history.time_seconds)[start_idx:end_idx],
    np.array(train_sim.history.velocity_meters_per_second)[start_idx:end_idx],
    label='achieved'
)
ax[-1].plot(
    np.array(train_sim.history.time_seconds)[start_idx:end_idx],
    np.array(train_sim.history.speed_target_meters_per_second)[
        start_idx:end_idx],
    label='target'
)
ax[-1].plot(
    np.array(train_sim.history.time_seconds)[start_idx:end_idx],
    np.array(train_sim.history.speed_limit_meters_per_second)[
        start_idx:end_idx],
    label='limit'
)
ax[-1].legend()
ax[-1].set_xlabel('Time [s]')
ax[-1].set_ylabel('Speed [m/s]')

# %%

# print composition of consist
for i, loco in enumerate(train_sim.loco_con.loco_vec.tolist()):
    print(f'locomotive at position {i} is {loco.loco_type()}')

# %% Sweep of BELs

bel = alt.Locomotive.default_battery_electic_loco()
diesel = alt.Locomotive.default()

loco_cons = [
    alt.Consist(
        [bel] * n_bels + [diesel] * (5 - n_bels),
        save_interval,
    ) for n_bels in range(0, 6)
]

train_sims = [get_train_sim(loco_con) for loco_con in loco_cons]

for i, ts in enumerate(train_sims):
    try:
        ts.walk()
        train_sims[i] = ts
    except RuntimeError as e:
        train_sims[i] = e

    ts.to_file('speed_limit_train_sim_results_{}.json'.format(i))
# %%