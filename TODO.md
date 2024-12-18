
# Ideas, notes and more

## Ideas
- Write equalizer similar thing to separate high / mid / low and show each on one sheet
- Normalize chroma, when running on chunks, with running average; otherwise it picks up noise due to normalization on chromagram
- Add some controls to player: one button to see what keys are available; then connect all important parameters to keys for stream processing
- Optimize the hell out of ArcNotes

## Todos
- Make that pygame message is not printed (either set env var to suppress or redirect output on import... both not good solutions)
- Write documentation with overview over the library's parts
- Write some usage examples
- Make fullscreen optional / flag, otherwise can provide width/height
- Make clones=int an arg and use it
- Allow to list and select audio source devices

## Notes

### Good settings for chroma_CQT
CHUNK = 1024  # multiple of SLIDE_LENGTH
CARRYOVER = 10
REFILL = 1
LOOPS = 100 * 5
SLIDE_LENGTH = 512


### Insights into required speed
- !WARNING: When processing runtime > buffer_replenish_multiplier * CHUNK / RATE, then the notes will slowly get more and more delayed
- potential solution: discard older notes, always empty audio buffer until no more to get
- !WARNING: buffer_replenish_multiplier * CHUNK / RATE is minimum delay between displays - should be <= 0.02s to perceive as real time

### How to connect an (audio) sink to a source and more (in Windows VirtualCable)
1. Create virtual cables, ny sound played to "virtual_speaker" will be sent to "virtual_mic"
```
pactl load-module module-null-sink sink_name="virtual_speaker" sink_properties=device.description="virtual_speaker"
pactl load-module module-remap-source master="virtual_speaker.monitor" source_name="virtual_mic" source_properties=device.description="virtual_mic"
```
2. Connect to your sound card to also listen to whatever is played
```
pactl load-module module-loopback source="virtual_mic" sink=alsa_output.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__hw_sofhdadsp__sink
pactl load-module module-loopback source="virtual_mic" sink=alsa_output.pci-0000_00_1f.3.analog-stereo
```
3. Select "virtual_speaker" resp. "virtual_mic" as your default devices in the audio settings; p.open() will automatically use the default input device

Further commands to remember
```
pactl list sources  # prints audio sources (micros and co) / in
pactl list sinks  # prints audio sinks (speakers and co) / out
pactl load-module module-loopback  # enable loopback for pulseaudio to listen to the output of the PC
pactl load-module module-lopback latency_msec=1
pactl list modules  # list all modules with their ids
pactl info 34  # print details about module with this id
pactl unload-module 24  # unload module with this id
```
