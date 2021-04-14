# timequota

```python
from timequota import TimeQuota

tq = TimeQuota(69)

# ...

tq.update()

for i in range(∞):

    # ...

    exceeded = tq.track()
    if exceeded:
        # ...
        break
```

[[Demo Notebook]](https://github.com/AravRS/timequota/blob/main/demo.ipynb)
[[Changelog]](https://github.com/AravRS/timequota/blob/main/CHANGELOG.md)
[[GitHub]](https://github.com/AravRS/timequota)
