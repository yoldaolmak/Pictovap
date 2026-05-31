# YOOS-VIL Runtime

Active server path: `/YOOS-VIL`

Use the project venv:

```bash
cd /YOOS-VIL
./setup_runtime.sh
./yoos_vil_health.py
./yo_cli.sh "5 foto yo 21312"
```

Global shortcuts:

```bash
yoos-vil "5 foto yo 21312"
yoos-vil-health
yoos-vil-setup
```

Runtime paths:

- VIL input folder: `/root/Downloads/VIL`
- Visual memory DB: `/YOOS-VIL/data/visual_memory.db`
- Project env: `/YOOS-VIL/.env` with mode `600`

The old active copy remains at `/root/YO_OS_VIL/YO_OS_VIL` as a fallback snapshot.
