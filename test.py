from subprocess import run

value = "hello from rbw"

run(
    ["wl-copy", "--type", "text/plain"],
    input=value,
    text=True,
    check=True,
)

print("wl-copy returned")
