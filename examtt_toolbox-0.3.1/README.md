# Italian ExamTT Validator 

This package provides a few utilities for handling the Italian Examination Timetabling problem.
Namely, it allows to validate a problem instance or a solution against an instance. 


```bash
examtt_toolbox --help
```

Currently it supports the following operations:

### `validate-instance`

Given an instance in `json` format it states whether the instance is valid and computes a few 
instance features.

### `validate-solution`

Given an instance, in `json` format, and a solution either in `json` or in `datazinc` format, it verifies  whether the solution 
is valid w.r.t. the instance and computes a few solution features.
