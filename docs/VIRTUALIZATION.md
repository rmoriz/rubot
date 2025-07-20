# Rubot Virtualization Guide

## Running Rubot in Virtual Machines

When running Rubot in virtualized environments, there are important considerations regarding CPU architecture and PyTorch compatibility.

### CPU Architecture Compatibility

**⚠️ Important:** When running Rubot in a virtual machine, avoid using the `qemu64` CPU architecture as it can cause PyTorch to break.

**Recommended Solution:** Use the host CPU architecture for your Rubot VM instead of the generic `qemu64` architecture.

### Why This Matters

Rubot uses Docling for PDF processing, which in turn relies on PyTorch for various machine learning operations including:
- OCR (Optical Character Recognition) with EasyOCR
- Document structure analysis
- Image processing

The `qemu64` CPU architecture is a generic, lowest-common-denominator CPU model that lacks many modern CPU features that PyTorch expects and optimizes for. This can lead to:
- Runtime errors during PyTorch operations
- Crashes during document processing
- Poor performance or hanging during OCR operations

### Configuration Examples

#### QEMU/KVM
Instead of:
```bash
-cpu qemu64
```

Use:
```bash
-cpu host
```

Or specify your actual CPU model:
```bash
-cpu Skylake-Client
```

#### VirtualBox
- Go to VM Settings → System → Processor
- Enable "Enable PAE/NX" 
- Consider enabling "Enable VT-x/AMD-V" if available

#### VMware
- Use "Virtualize Intel VT-x/EPT or AMD-V/RVI" option
- Avoid compatibility mode settings that might limit CPU features

### Alternative: CPU-Only Mode

If you must use `qemu64` or encounter PyTorch issues, you can force Rubot to use CPU-only mode:

```bash
export DOCLING_USE_CPU_ONLY=true
```

Or in your `.env` file:
```
DOCLING_USE_CPU_ONLY=true
```

This disables GPU acceleration and uses more conservative CPU operations that are compatible with limited CPU architectures.

### Performance Considerations

- **Host CPU architecture**: Best performance, full feature support
- **Specific CPU model**: Good performance, most features supported  
- **CPU-only mode**: Slower but more compatible
- **qemu64**: Not recommended, may cause failures

### Troubleshooting

If you encounter PyTorch-related errors in a VM:

1. Check your VM's CPU configuration
2. Try enabling `DOCLING_USE_CPU_ONLY=true`
3. Reduce processing load with `MAX_PDF_PAGES=10`
4. Disable OCR with `DOCLING_DO_OCR=false` if needed

### Related Configuration

See the main configuration documentation for other Docling/PyTorch related settings:
- `DOCLING_USE_CPU_ONLY`: Force CPU-only processing
- `DOCLING_OCR_ENGINE`: Choose OCR engine (easyocr, tesseract, rapidocr)
- `DOCLING_DO_OCR`: Enable/disable OCR processing
- `DOCLING_BATCH_SIZE`: Control memory usage during processing