# assumes a python environment has been created and activated
(cd rust/altrios-core/ && cargo test) && \
# pip install -qe ".[dev]" && \ 
maturin develop --release && \
pytest -v tests && \
(cd applications/demos/ && python sim_manager_demo.py && python rollout_demo.py)