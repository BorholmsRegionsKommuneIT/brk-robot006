# brk-robot006

rpa flow "Pension til timelønnede"

`main_refactored.py` is the new refactored robot that is easier to think about. It does not put everything into 
a note column. Instead it returns boolean pandas series corresponding to the flowchart. Many small composable functions FTW. 


-----

**Table of Contents**

- [brk-robot006](#brk-robot006)
  - [Contribute](#contribute)
  - [License](#license)
  - [Docs](#docs)


## Contribute 

This project uses [hatch](https://hatch.pypa.io/latest/) as [build-backend](https://packaging.python.org/en/latest/glossary/#term-Build-Backend). Install it globally and run `hatch shell` to create a virtual env.

Inside the virtiual env, install dependencies:

```console
pip install .
```

## License

`brk-robot006` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.


## Docs
Implementeringen adskiller sig fra beskrivelsen i Powerpointen.

*Beskrivelse*: for hver medarbejder kør igennem alle checks.

*Implementering*: For hvert check kør igennem alle medarbejdere. 