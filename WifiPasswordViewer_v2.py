"""
List saved Wi-Fi profiles and show the selected profile's saved key.

Run this script on a Windows computer where you have permission to view
the saved wireless network credentials.
"""

import subprocess
import sys


def run_netsh(*arguments: str) -> str:
    """Run netsh without a shell, returning its output or raising an error."""
    result = subprocess.run(
        ["netsh", *arguments],
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(message or f"netsh exited with code {result.returncode}")
    return result.stdout


def get_profile_names(output: str) -> list[str]:
    """Extract profile names from `netsh wlan show profiles` output."""
    names = []
    for line in output.splitlines():
        if "All User Profile" in line or "Current User Profile" in line:
            _, separator, name = line.partition(":")
            if separator and name.strip():
                names.append(name.strip())
    return names


def main() -> int:
    try:
        profiles_output = run_netsh("wlan", "show", "profiles")
        profiles = get_profile_names(profiles_output)
    except (OSError, RuntimeError) as error:
        print(f"Could not read saved Wi-Fi profiles: {error}", file=sys.stderr)
        return 1

    if not profiles:
        print("No saved Wi-Fi profiles were found.")
        return 0

    print("Saved Wi-Fi profiles:")
    for index, name in enumerate(profiles, start=1):
        print(f"[{index}] {name}")

    try:
        choice = int(input("Enter the profile number to show its saved password: "))
    except ValueError:
        print("Please enter a number from the list.", file=sys.stderr)
        return 2
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return 0

    if not 1 <= choice <= len(profiles):
        print("That number is not in the list.", file=sys.stderr)
        return 2

    profile = profiles[choice - 1]
    try:
        details = run_netsh("wlan", "show", "profile", profile, "key=clear")
    except (OSError, RuntimeError) as error:
        print(f"Could not read the password for {profile!r}: {error}", file=sys.stderr)
        return 1

    # Windows displays the saved key on the English-language "Key Content" line.
    # Show the full profile details when that label is absent (for example,
    # on a localized Windows installation or an open network).
    for line in details.splitlines():
        label, separator, value = line.partition(":")
        if separator and label.strip() == "Key Content":
            print(f"Password for {profile}: {value.strip() or '(none saved)'}")
            break
    else:
        print(f"Password details for {profile}:\n{details}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
