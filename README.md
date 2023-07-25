# sat-city Satellite Data City Summary

### Authors:
 - Arthur Elmes (arthur.elmes@gmail.com)
 - Bily Brown (bilyhasemail@gmail.com)


 ### Environment
 You'll need to use a Python runtime environment with the required libraries.

 There are two approaches, one of which may be deprecated soon to avoid confusion
 and verision divergences:

 #### Conda
 The `conda` environment and package managemener can be used to create an
 environment with the required libraries.
 The installation steps are here:
 https://docs.conda.io/projects/conda/en/latest/user-guide/install/.

 Note that Miniconda is sufficient; Anaconda is a larger application. Either is fine,
 but Miniconda is mini.

 With conda installed, run the following lines in the terminal:
```
conda env create -f sat-city-conda-env.yml
conda activate sat-city
```

 #### pyenv+pip-tools
 `pyenv` uses `pip`'s native virtual environment approach (`venv`) to maintain
 isolated python environments on a per-project basis. This allows each project
 to maintain its own python interpreter and libraries that are separate from
 the system python interpreter and all other projects. `pip-compile`, part of
 `pip-tools`, can be used to create a complete `requirements.txt` using a minimally
 specified `requirements.in`. This is similar to `conda`, but without requiring
 the larger `conda` overhead.

 The `pyenv` installation instructions are here:
 https://github.com/pyenv/pyenv?search=1#usage
 Follow the directions here to create a python
 environment specific to this project, using the
 `pyenv local ...` command:
 https://github.com/pyenv/pyenv?search=1#usage.
 This will create a local file called `.python-version` that will activate your chosen
 python environment when you `cd` into this project's
 root dir. Use python version 3.10.

 Using `pip-compile` requires installation of `pip-tools` via
 pip. Then, use `pip-compile -o requirements.txt --resolver=backtracking requirements.in` to
 create a requirements.txt file with all dependencies wrangled. The
 idea for requirements.in is to specify and pin requirements loosely;
 `pip-compile` then creates a fully specified, tightly-pinned environment
 definition. Then, use the regular `pip install -r requirements.txt` to
 actually install all the libraries.
