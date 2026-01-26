import os
import subprocess
import sys
import platform

# ==========================================
# 🛑 PASTE YOUR FOLDER PATH BELOW
FOLDER_PATH = r'/Users/calebstone/Library/CloudStorage/OneDrive-Embry-RiddleAeronauticalUniversity/Semester 8/Sys Research/Drone Logs/FlightRecordsdjifly'

# 🛑 PASTE YOUR DJI APP KEY BELOW (Required for 2021+ logs)
# Register at https://developer.dji.com/ -> Create App -> Mobile SDK -> Copy App Key
DJI_API_KEY = "e318d104a45165d0ddd53011e93347e"  # e.g., "78df9a87d89f7a89d7f..."
# ==========================================

# ==========================================
# 🛠 TOOL CONFIGURATION
TOOL_NAME = "dji-log"
# ==========================================

def run_conversion():
    # --- 1. PATH CHECKS ---
    if not os.path.exists(FOLDER_PATH):
        print(f"❌ ERROR: Could not find folder: {FOLDER_PATH}")
        return

    tool_full_path = os.path.join(FOLDER_PATH, TOOL_NAME)
    
    if not os.path.exists(tool_full_path):
        print(f"❌ ERROR: Could not find the tool '{TOOL_NAME}'")
        return

    # --- 2. PERMISSIONS ---
    if platform.system() != "Windows":
        try:
            subprocess.run(["xattr", "-d", "com.apple.quarantine", tool_full_path], 
                          stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            os.chmod(tool_full_path, 0o755)
        except Exception:
            pass

    # --- 3. FILE SCAN ---
    files = [f for f in os.listdir(FOLDER_PATH) if f.lower().endswith(".txt")]
    print(f"📂 Found {len(files)} flight logs.")

    if not DJI_API_KEY:
        print("\n⚠️  WARNING: No DJI API Key provided.")
        print("   Logs from 2021 onwards will likely FAIL due to encryption.")
        print("   Get a key at developer.dji.com to unlock them.\n")
    
    # --- 4. CONVERSION LOOP ---
    print("🚀 Starting conversion...\n")
    
    count = 0
    fail_count = 0
    
    for filename in files:
        input_path = os.path.join(FOLDER_PATH, filename)
        output_csv = os.path.join(FOLDER_PATH, filename.replace(".txt", ".csv"))
        
        # CHECK FOR EXISTING FILES
        if os.path.exists(output_csv):
            if os.path.getsize(output_csv) < 100: 
                # If file is tiny, it's likely a failed previous run, retry it.
                pass 
            else:
                # print(f"⏩ Skipping {filename} (Already exists)")
                continue

        try:
            # Build Command
            command = [tool_full_path, input_path, "--csv", output_csv]
            
            # Add API key if provided
            if DJI_API_KEY:
                command.extend(["--api-key", DJI_API_KEY])

            print(f"🔨 Processing {filename}...", end="\r")
            
            process = subprocess.run(
                command, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            
            print(f"✅ Converted: {filename}        ") 
            count += 1
            
        except subprocess.CalledProcessError as e:
            # Clean up empty file if failed
            if os.path.exists(output_csv) and os.path.getsize(output_csv) < 100:
                os.remove(output_csv)
                
            error_msg = e.stderr.decode('utf-8').strip()
            
            if "panicked" in error_msg or "api-key" in error_msg:
                 print(f"🔒 ENCRYPTED: {filename} (Needs API Key)     ")
            else:
                 print(f"❌ FAILED: {filename}           ")
                 print(f"   Reason: {error_msg.splitlines()[0] if error_msg else 'Unknown'}")
            
            fail_count += 1

    print(f"\n🎉 Finished! Converted {count} new files.")
    if fail_count > 0 and not DJI_API_KEY:
        print(f"⚠️  {fail_count} files failed (likely encryption). Please add an API Key.")

if __name__ == "__main__":
    run_conversion()