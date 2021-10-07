[![logo](https://user-images.githubusercontent.com/43105734/136433076-bcbcf0d3-a772-443b-9842-3547102dfd34.png)](https://aravrs.github.io/timequota/)

# timequota

Manage the time of your python script.

```python
from timequota import TimeQuota

tq = TimeQuota(2, "h")

# ...

tq.update()

for i in range(100):

    # ...

    will_exceed_time = tq.track()
    if will_exceed_time:
        # ...
        break
```
