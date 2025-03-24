#!/bin/python
import csv
file_name = "in_reduced.csv"
out_file_name = "esphome.yml"

with open(file_name, "r") as fp:
 # lines = fp.readlines()
 lines = csv.reader(fp, delimiter=",", quotechar = "'")
 sensors = list()
 on_frames = list()
 for l in list(lines)[1:]:
  # 0: Device
  # 1:Group
  # 2 Module
  # 3Name
  # 4 ID
  # 5 Brunner_Name
  # 6 Unit
  # 7 Scale
  # 8 Alternate_ID
  # 9 Annotations
  # 10 Certainty
  # 11 State Class
  # 12 Device Class
  #13 Postcall
  # info = l.split(",")
  info = l
  s_id = "_".join(info[:4])
  s_id = s_id.replace(" ", "_")
  s_id = s_id.replace("-", "_").strip()
  if s_id.endswith("_"):
   s_id = s_id[:-1]
  s_name = " ".join(info[:4]).strip()

  sensors.append(f"""
  - platform: template
    name: "{s_name}"
    id: "{s_id}"
    state_class: {info[11]}
    unit_of_measurement: "{info[6]}"
    lambda: |-
        return id({s_id}).state;
    update_interval: 10s""")
  device_class = info[12].strip()
  if device_class:
   sensors.append(f"\n    device_class: {device_class}")
  # https://esp32.com/viewtopic.php?t=13325
  # https://www.csselectronics.com/pages/can-dbc-file-database-intro
  # https://esphome.io/components/canbus.html
  on_frames.append(f"""
                 case {info[4]}: 
                 {{
                     union BytesToNumbers
                     {{
                       uint8_t bytes[2] = {{0,0}};
                       short val;
                      }} bytesToNumbers;  
                     bytesToNumbers.bytes[0] = x[2];
                     bytesToNumbers.bytes[1] = x[1];
                     float v = bytesToNumbers.val;
                     {"v = v * " + info[7] + ";"  if info[7] else ""}
                     id({s_id}).state = v;
{info[13]}
                     break;
                 }}""")
 out_lines = list()
 out_lines.append("sensor:\n")
 out_lines.append("  - platform: uptime\n")
 out_lines.append("    name: Uptime Sensor\n")
 out_lines.extend(sensors)
 out_lines.append("""
canbus:
  - platform: esp32_can
    tx_pin: GPIO5
    rx_pin: GPIO17
    can_id: 4
    bit_rate: 125kbps
    on_frame:
    - can_id: 0x0
      can_id_mask: 0x0
      use_extended_id: true
      then:
      - lambda: |-
           if(x.size() > 3) {
             switch(can_id) {""")
 out_lines.extend(on_frames)
 out_lines.append("""
                default:
                        // ESP_LOGD("canbus_unhandled_id with non-zero value", "%x", can_id);
                    break;
                 }
               }""")
 with open(out_file_name, "w") as fp2:
  fp2.writelines(out_lines)
