## Installing Verus

Follow these steps to install Verus from source:

```bash
git clone https://github.com/verus-lang/verus.git
cd verus
git checkout ddc66116aa7a844a9e19cc50922fe85c84b8b4a5
# NOTE: the following commands must be executed in the same shell
./source/tools/get-z3.sh
source tools/activate
vargo build --release
```

After installation, the Verus executable will be located at `source/target-verus/release/verus`.

## Running Rust Code in the ST Benchmark

Before running any Rust code from the ST benchmark, you need to build the `deps_hack` crate:

```bash
cd ST_test/deps_hack

cargo +1.88.0 build
```

Next, configure Verus with the necessary external arguments to validate the Rust code. You can specify these arguments either directly in your bash command or in a configuration file:

```bash
cd ST_test

verus \
  -L dependency=deps_hack/target/debug/deps \
  --extern deps_hack=deps_hack/target/debug/libdeps_hack.rlib \
  ST__inv_L_active_metadata_set_after_crash.rs  # example rust file
```

Alternatively, you can define these arguments in a configuration file:
```json
{
"verus_args": [
    "-L", "dependency=Dataset/VeruSAGE_overall_Dataset_RustFiles/ST_test/deps_hack/target/debug/deps",
    "--extern=deps_hack=Dataset/VeruSAGE_overall_Dataset_RustFiles/ST_test/deps_hack/target/debug/libdeps_hack.rlib"
],
}
```

**Note:** When using a configuration file, you need to modify `main.py` in VeruSAGE to parse the `verus_args`:
```python
# First, load from config file if present
if hasattr(config, 'verus_args') and config.verus_args:
    verus_args = config.verus_args if isinstance(config.verus_args, list) else shlex.split(config.verus_args)
# Then, override/extend with command line args if provided
if args.verus_args:
    verus_args = shlex.split(args.verus_args)
```