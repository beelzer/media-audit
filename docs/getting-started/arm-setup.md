# ARM Architecture Support

Media-audit fully supports ARM-based systems including Apple Silicon Macs, Raspberry Pi, and other ARM Linux devices. This guide covers platform-specific setup instructions.

## Supported ARM Platforms

- **macOS (Apple Silicon)**: M1, M2, M3 series processors
- **Linux ARM64**: Raspberry Pi 4/5, AWS Graviton, Ampere Altra
- **Linux ARMv7**: Raspberry Pi 3, older ARM devices

## Installation

### Python Installation

Media-audit requires Python 3.13+. Most ARM platforms have native Python support:

#### macOS (Apple Silicon)

```bash
# Using Homebrew (native ARM build)
brew install python@3.13

# Verify architecture
python3 -c "import platform; print(platform.machine())"
# Should output: arm64
```

#### Linux ARM (Raspberry Pi OS, Ubuntu)

```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Install Python 3.13
sudo apt install python3.13 python3.13-venv python3-pip

# Verify architecture
python3 -c "import platform; print(platform.machine())"
# Should output: aarch64 or armv7l
```

### FFmpeg Installation

FFmpeg is required for media analysis. Install the appropriate version for your platform:

#### macOS (Apple Silicon)

```bash
# Native ARM64 build via Homebrew
brew install ffmpeg

# Verify installation
ffmpeg -version
ffprobe -version
```

#### Linux ARM64 (64-bit ARM)

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# For latest version, use snap
sudo snap install ffmpeg

# Verify installation
ffmpeg -version | grep "gcc.*aarch64"
```

#### Linux ARMv7 (32-bit ARM)

```bash
# Raspberry Pi OS / Raspbian
sudo apt install ffmpeg

# For hardware acceleration on Raspberry Pi
sudo apt install ffmpeg libraspberrypi-bin

# Verify installation
ffmpeg -version | grep "gcc.*arm"
```

#### Building FFmpeg from Source (Optional)

For optimal performance on specific ARM hardware:

```bash
# Install build dependencies
sudo apt install build-essential git pkg-config \
  libx264-dev libx265-dev libvpx-dev

# Clone and build FFmpeg
git clone https://github.com/FFmpeg/FFmpeg.git
cd FFmpeg
./configure --enable-gpl --enable-libx264 --enable-libx265 \
  --enable-libvpx --enable-neon  # NEON for ARM optimization
make -j$(nproc)
sudo make install
```

## Media-Audit Installation

Install media-audit using pip:

```bash
# Install from PyPI
pip install media-audit

# Or install from source
git clone https://github.com/yourusername/media-audit.git
cd media-audit
pip install -e .
```

## Performance Optimization

### Concurrent Workers

Media-audit automatically detects the optimal number of workers for your ARM platform:

- **Apple Silicon**: Up to 8 concurrent workers (excellent performance)
- **ARM Linux**: Up to 4 concurrent workers (balanced for power efficiency)

You can override the auto-detection:

```bash
# Use specific worker count
media-audit scan --workers 6

# Use auto-detection (default)
media-audit scan --workers 0
```

### Memory Considerations

ARM devices often have limited RAM. Adjust workers based on available memory:

| Device | RAM | Recommended Workers |
|--------|-----|-------------------|
| Raspberry Pi 4 (2GB) | 2GB | 2 |
| Raspberry Pi 4 (4GB) | 4GB | 3-4 |
| Raspberry Pi 4 (8GB) | 8GB | 4-6 |
| Mac Mini M1 (8GB) | 8GB | 4-6 |
| Mac Studio M2 (32GB) | 32GB | 8-12 |

### Storage Performance

For Raspberry Pi and similar devices:

1. **Use SSD storage** when possible for media libraries
2. **Enable caching** to reduce repeated scans:

   ```bash
   media-audit scan --cache-dir /path/to/ssd/cache
   ```

3. **Network storage**: Mount NAS shares with optimal settings:

   ```bash
   # For SMB/CIFS
   sudo mount -t cifs //nas/media /mnt/media -o vers=3.0,cache=loose,noserverino

   # For NFS
   sudo mount -t nfs -o rsize=131072,wsize=131072 nas:/media /mnt/media
   ```

## Platform-Specific Notes

### Raspberry Pi

1. **Enable GPU memory split** for better video processing:

   ```bash
   sudo raspi-config
   # Advanced Options > Memory Split > 256
   ```

2. **Overclock for better performance** (Pi 4/5):

   ```bash
   # Edit /boot/config.txt
   over_voltage=6
   arm_freq=2000
   gpu_freq=750
   ```

3. **Use hardware-accelerated FFmpeg** when available:

   ```bash
   # Check for hardware acceleration
   ffmpeg -hwaccels
   ```

### Apple Silicon

1. **Rosetta 2 is NOT required** - media-audit runs natively on ARM64

2. **Verify native execution**:

   ```bash
   # Check if running native ARM
   ps aux | grep python
   # Should show "arm64" in the process info
   ```

3. **Use native Homebrew** (installed in `/opt/homebrew`):

   ```bash
   which brew
   # Should output: /opt/homebrew/bin/brew
   ```

## Troubleshooting

### Common Issues

#### FFmpeg not found

```bash
# Add to PATH in ~/.bashrc or ~/.zshrc
export PATH="/usr/local/bin:$PATH"  # Linux
export PATH="/opt/homebrew/bin:$PATH"  # macOS ARM
```

#### Slow performance on network drives

- Use wired Ethernet instead of Wi-Fi when possible
- Adjust worker count: `--workers 2`
- Enable aggressive caching

#### Memory errors on small devices

- Reduce workers: `--workers 1`
- Process smaller directories individually
- Increase swap space:

  ```bash
  sudo dphys-swapfile swapoff
  sudo nano /etc/dphys-swapfile
  # Set CONF_SWAPSIZE=2048
  sudo dphys-swapfile setup
  sudo dphys-swapfile swapon
  ```

### Platform Detection

Check detected platform:

```python
from media_audit.shared.platform_utils import get_platform_info
import pprint

pprint.pprint(get_platform_info())
```

Output example:

```python
{
    'system': 'Linux',
    'platform': 'linux',
    'architecture': 'aarch64',
    'processor': 'ARM Cortex-A72',
    'python_version': '3.13.0',
    'is_arm': 'True',
    'is_x86': 'False',
    'is_64bit': 'True'
}
```

## CI/CD Support

Media-audit's CI pipeline includes ARM testing:

- **Native ARM runners**: macOS M1/M2 (GitHub Actions)
- **QEMU emulation**: ARM64 Linux testing
- **Cross-compilation**: ARM binary builds

## Contributing

When contributing ARM-specific improvements:

1. Test on multiple ARM platforms if possible
2. Document platform-specific behavior
3. Consider power efficiency in addition to performance
4. Use platform detection for conditional optimizations

## Additional Resources

- [FFmpeg ARM Optimization Guide](https://trac.ffmpeg.org/wiki/HWAccelIntro)
- [Python on ARM Performance](https://realpython.com/python-arm-performance/)
- [Raspberry Pi Media Server Guide](https://www.raspberrypi.org/documentation/)
- [Apple Silicon Optimization](https://developer.apple.com/documentation/apple-silicon)
