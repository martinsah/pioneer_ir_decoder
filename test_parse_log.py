import sys
import argparse
from decode_pronto_hex import parse_pronto_log, decode_pronto_hex, timing_histogram, print_histogram, reduce_histogram, meanify_messages, convert_to_binary, convert_to_hex, print_binary_messages
from colorama import Fore, Style, init
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse and decode Pronto hex log messages')
    parser.add_argument('--start-bits', type=int, default=0, dest='start_bits',
                        help='Number of bits to skip at the start of each binary message (default: 0)')
    parser.add_argument('--stop-bits', type=int, default=0, dest='stop_bits',
                        help='Number of bits to skip at the end of each binary message (default: 0)')
    parser.add_argument('--show-odd-even', type=bool, default=False, dest='show_odd_even',
                        help='Show odd and even messages separately')

    args = parser.parse_args()
    start_bits = args.start_bits
    stop_bits = args.stop_bits
    show_odd_even = args.show_odd_even
    log_text = sys.stdin.read()
    hex_numbers = parse_pronto_log(log_text)
    init()
    print(Fore.GREEN + "Extracted hex numbers:" + Style.RESET_ALL)
    print(hex_numbers)
    print(f"\nTotal hex numbers found: {len(hex_numbers.split())}")
    
    # Decode the hex numbers
    try:
        messages = decode_pronto_hex(hex_numbers)
        print(Fore.GREEN + f"\nDecoded {len(messages)} message(s):" + Style.RESET_ALL)
        for i, (timings, frequency) in enumerate(messages):
            print(Fore.GREEN + f"\nMessage {i}: (Freq: {frequency} Hz): Length: {len(timings)}  " + Style.RESET_ALL)
            print(f"  Timings: {timings}")
        hist = timing_histogram(messages)
        print_histogram(hist)
        reduced_hist = reduce_histogram(hist, 10)
        print(Fore.GREEN + f"\nReduced histogram: {len(reduced_hist)} unique values" + Style.RESET_ALL)
        print(reduced_hist)

        messages = meanify_messages(messages, reduced_hist, 10)
        print(Fore.GREEN + f"\nMeanified {len(messages)} message(s)" + Style.RESET_ALL)
        for i, (timings, frequency) in enumerate(messages):
            print(Fore.GREEN + f"\nMessage {i}: (Freq: {frequency} Hz): Length: {len(timings)}" + Style.RESET_ALL)
            print(f"  Timings: {timings}")
        
        # Cross-correlate and highlight differences
        #print_message_timing_comparison(messages)

        binary_messages = convert_to_binary(messages, start_bits, stop_bits)

        # Print binary messages
        if show_odd_even:
            print_binary_messages(binary_messages, 0, 2)
            print_binary_messages(binary_messages, 1, 2)
        else:   
            print_binary_messages(binary_messages, 0, 1)

        # Convert binary messages to hex and print with checksum
        old_hex_message = ""
        old_hex_message2 = ""
        hex_message = ""
        hex_message2 = ""
        for i in range(0, len(binary_messages), 2):
            binary_message1 = binary_messages[i]
            binary_message2 = binary_messages[i+1]
            old_hex_message = hex_message
            old_hex_message2 = hex_message2
            (hex_message, checksum) = convert_to_hex(binary_message1, lsbfirst=True, wordsize=8)
            (hex_message2, checksum2) = convert_to_hex(binary_message2, lsbfirst=True, wordsize=8)
            checksum = f"{checksum+15:02X}"    # convert to hex and pad with 0s
            checksum2 = f"{checksum2:02X}"    # convert to hex and pad with 0s
            if i<2:
                old_hex_message = [0] * len(hex_message)
                old_hex_message2 = [0] * len(hex_message2)
            print(Fore.GREEN + f"[{i}] " + Style.RESET_ALL, end="")
            for (new, old) in zip(hex_message, old_hex_message):
                if new != old:
                    print(Fore.RED + f"{new} "+ Style.RESET_ALL, end="") 
                else:
                    print(f"{new} "+ Style.RESET_ALL, end="") 
            print(Fore.GREEN + f" Checksum: {checksum} " + Style.RESET_ALL, end="")
            print(Fore.GREEN + f" [{i+1}] " + Style.RESET_ALL, end="")
            for (new, old) in zip(hex_message2, old_hex_message2):
                if new != old:
                    print(Fore.RED + f"{new} "+ Style.RESET_ALL, end="") 
                else:
                    print(f"{new} "+ Style.RESET_ALL, end="") 
            print(Fore.GREEN + f" Checksum: {checksum2} " + Style.RESET_ALL, end="")
            print(Style.RESET_ALL)


        print(f"\n")
    except ValueError as e:
        print(f"\nError decoding: {e}")


