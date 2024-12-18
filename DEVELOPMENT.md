# Development
This document is intended to serve as starting point for developing further components. It explains the main program architecture aka how the components interact with each other, as well as the most important concepts and requirements.

## Architecture
The `game` visualizes `audio features` extracted from one or more `audio streams`. The main components and their interactions are shown here.

**game (main process)**
```
canvas = render(game)
blit(screen, canvas)
for _ in range(n_streams):
    ft = queue.pop()
    canvas = render(ft)
    blit(screen, canvas)
```

**processors (one thread per stream)**
```
chunk = read_stream()
ft = process(chunk)
queue.put(ft)
```


## Runtime requirements
Most components of `circle_dance` are subject to one or two runtime requirements. On the one hand, there is the reading of the `audi stream`: if the read audio samples are not processed fast enough, the input buffer will overflow. On the other hand, the `game`'s screen must update fast enough to ensure a smooth visualization.

In this section, the two duration requirements are derived and their compuation, which depends on various factors, described.

```
n_streams = {1,2,...}
sr = 42000 | 21000

n_new_samples = 1024
n_carryover_samples = 2048
chunk = [carryover_samples] + [new_samples]

max_processing_duration = n_new_samples/sr [s]  # speed required such that audio stream buffer doesn't overflow
fps = 30 | 60  # screen update speed required for a smooth visualization
max_render_duration = 1/fps [s]
```

The principal components highlighted in the architecture overview above are subject to these duration constraints.

```
time[process(chunk)] < max_processing_duration
time[render(all)] < min(max_tick_duration, max_render_duration)
time[render(ft)] < min(max_tick_duration, max_render_duration) / n_streams
```

Note that the actual runtimes should be lower than the duration constraints, as the whole program produces some overhead, e.g. for communicating between threads.

### Exemplary runtime requirements

```
n_streams = 1
sr = 42000
n_new_samples = 1024
n_carryover_samples = 2048
fps = 30

max_processing_duration = 0.024380952s = 24.38ms
max_render_duration = 0.033333333s = 33.33ms
```

```
n_new_samples = 2048

max_processing_duration = 0.048761905s = 48.76ms
```

```
n_new_samples = 512

max_processing_duration = 0.012190476s = 12.19ms
```

```
fps = 60

max_render_duration = 0.016666667 = 16.66ms
```

## Alternative architecture
By moving the `audio feature` renderers into thread workers, the runtime requirements might be loosened somewhat in the case of multiple input streams.

**game (main process)**
```
canvas = render(game)
blit(screen, canvas)

for t in audio_feature_threads:
    t.run()

canvases = [t.wait() for t in audio_feature_threads]
for canvas in canvases:
    blit(screen, canvas)
```

**audio feature renderer (one thread per renderer)**
```
ft = queue.pop()
canvas = render(ft)
```

**processors (one thread per stream)**
```
chunk = read_stream()
ft = process(chunk)
queue.put(ft)
```

Note that a single processor can be linked to multiple audio feature renderers via dedicated queues.

In such a configuration, the runtime requirements qould change to:

```
time[process(chunk)] < max_processing_duration
time[render(all)] < min(max_tick_duration, max_render_duration)
time[render(ft)] < time[render(all)] < min(max_tick_duration, max_render_duration)
```
