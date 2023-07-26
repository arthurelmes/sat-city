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
 `pyenv` uses enables usage of multiple, isolated python interpreters on your
 system, which can be automatically activated on a per-project basis.
 When used with the `pyenv-virtualenv` plugin, you can create and manage isolated
 virtual environments.

 `pip-compile`, part of `pip-tools`, can be used to create a complete
 `requirements.txt` using a minimally specified `requirements.in`. This is similar
 to `conda`, but without requiring the larger `conda` overhead.

 The `pyenv` installation instructions are here:
 https://github.com/pyenv/pyenv?search=1#usage
 Use `pyenv install 3.10` to install python 3.10. You can install any set of python
 versions you need for your various projects -- this keeps them organized and prevents
 them from stepping on each other's toes.

 Then, in order to construct a virtual environmnet, `cd` into this project's root dir, and
 use `pyenv virtualenv 3.10 sat-city-env`. This will create a virtual environment (similar to
 a conda environment) into which you'll install the required libraries. It also creates a
 local file called `.python-version` that will activate your chosen python environment when
 you `cd` into this project's root dir.

 Using `pip-compile` requires installation of `pip-tools` via pip -- to do this, run
 `pip install -r requirements-dev.txt`.
 Then, use `pip-compile -o requirements.txt --resolver=backtracking requirements.in` to
 create a requirements.txt file with all dependencies wrangled. The
 idea for requirements.in is to specify and pin requirements loosely;
 `pip-compile` then creates a fully specified, tightly-pinned environment
 definition. Then, use the regular `pip install -r requirements.txt` to
 actually install all the libraries.
