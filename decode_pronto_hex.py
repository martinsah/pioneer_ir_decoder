import re
from collections import Counter
from colorama import Fore, Style, init
init()  
def decode_pronto_hex(pronto_hex):
    """
    Decodes a Pronto hex dump into a list of messages. Each message starts with 0000.

    Args:
        pronto_hex (str): The Pronto hex string (e.g., "0000 0067 0000 000d ...").

    Returns:
        list: A list of tuples, where each tuple is (timings_us, frequency) for one message.
              timings_us is a list of timing values in microseconds and frequency is the carrier frequency in Hz.
    """
    # Parse hex string into 16-bit words
    hex_values = pronto_hex.replace(" ", "").replace("\n", "")
    if len(hex_values) % 4 != 0:
        raise ValueError("Pronto hex string length must be a multiple of 4 characters (16-bit words).")

    words = []
    for i in range(0, len(hex_values), 4):
        words.append(int(hex_values[i:i+4], 16))

    if not words:
        return []

    messages = []
    i = 0
    
    while i < len(words):
        # Look for next message start (0000 at word 0 position)
        # Skip until we find a 0000 that could be a message start
        while i < len(words) and words[i] != 0x0000:
            i += 1
        
        if i >= len(words):
            break  # No more messages
        
        # Found potential message start at index i
        start_idx = i
        
        # Check if we have at least 4 words for the header
        if start_idx + 4 > len(words):
            break  # Not enough words for a complete message
        
        message_words = words[start_idx:start_idx + 4]
        
        # Pronto format: Word 0=format, Word 1=carrier frequency, Word 2=initial pairs, Word 3=repeat pairs
        if message_words[0] != 0x0000:
            # This shouldn't happen since we checked, but handle it
            i += 1
            continue
        
        initial_pairs = message_words[2]
        repeat_pairs = message_words[3]
        
        # Calculate expected message length: 4 header words + (initial_pairs * 2) + (repeat_pairs * 2)
        expected_length = 4 + (initial_pairs * 2) + (repeat_pairs * 2)
        
        # Calculate actual available length (don't go past end of words)
        available_length = min(expected_length, len(words) - start_idx)
        
        # Extract message (may be incomplete)
        message_words = words[start_idx:start_idx + available_length]
        
        # Check if we have at least the header
        if len(message_words) < 4:
            i += 1
            continue
        
        # Calculate time base: 0.2413 * carrier_freq_word microseconds per count
        time_base_us = 0.2413 * message_words[1] if message_words[1] != 0 else 1

        # Convert timing counts (words[4:]) to microseconds
        timing_data_counts = message_words[4:]
        timings_us = [int(round(count * time_base_us)) for count in timing_data_counts]

        # Calculate carrier frequency: 1000000 / (carrier_freq_word * 0.2413) Hz
        frequency = int(1000000 / (message_words[1] * 0.2413)) if message_words[1] != 0 else 0

        print(f"Frequency: {frequency} Hz")
        print(f"message_words[0]: {message_words[0]}")
        print(f"message_words[1]: {message_words[1]}")
        print(f"message_words[2]: {message_words[2]}")
        print(f"message_words[3]: {message_words[3]}")
        print(f"message_words[4:]: {message_words[4:]}")
        print(f"timings_us: {timings_us}")
        print(f"time_base_us: {time_base_us}")
        print(f"timing_data_counts: {timing_data_counts}")
        print(f"message_words: {message_words}")

        messages.append((timings_us, frequency))
        
        # Move to the position after this message
        # Use expected_length to properly advance, even if message was incomplete
        i = start_idx + expected_length

    return messages


def parse_pronto_log(log_text):
    """
    Parses log text by removing timestamps and headers, extracting only four-character hex numbers.
    
    Args:
        log_text (str): The log text containing timestamps, headers, and hex values.
    
    Returns:
        str: A string containing just the four-character hex numbers, space-separated.
    """
    hex_pattern = r'\b[0-9A-Fa-f]{4}\b'
    hex_matches = re.findall(hex_pattern, log_text)
    return ' '.join(hex_matches)


def timing_histogram(messages):
    """
    Creates a statistical histogram of unique timing values across all messages.
    
    Args:
        messages (list): A list of tuples from decode_pronto_hex, where each tuple is
                        (timings_us, frequency) for one message.
    
    Returns:
        dict: A dictionary mapping timing values (in microseconds) to their occurrence counts.
              Keys are timing values, values are counts. Sorted by timing value.
    """
    if not messages:
        return {}
    
    # Collect all timing values from all messages
    all_timings = []
    for timings_us, _ in messages:
        all_timings.extend(timings_us)
    
    # Create histogram using Counter
    histogram = Counter(all_timings)
    
    # Return as sorted dictionary
    return dict(sorted(histogram.items()))

def reduce_histogram(hist, percentage_threshold):
    """
    Examine the histogram and reduce it to the elements that only differ by x% 
    
    Args:
        hist (dict): A dictionary mapping timing values to their occurrence counts,

    Returns:
        dict: A dictionary mapping timing values to their occurrence counts,
              typically from timing_histogram().
    """

    reduced_hist = {}
    for value in hist.keys():
        found_similar = False
        for existing_base_value in reduced_hist:
            # Check if 'value' is within 10% of 'existing_base_value'
            lower_bound = existing_base_value * (1 - percentage_threshold / 100)
            upper_bound = existing_base_value * (1 + percentage_threshold / 100)
            
            if lower_bound <= value <= upper_bound:
                reduced_hist[existing_base_value].append(value)
                found_similar = True
                break
                
        if not found_similar:
            # If no matching group found, create a new group
            reduced_hist[value] = [value]
    results = [] 

    for key, value in reduced_hist.items():
        results.append(int(sum(value) / len(value)))
    return results

def print_histogram(hist):
    """
    Prints a histogram dictionary in a readable format, one entry per line.
    
    Args:
        hist (dict): A dictionary mapping timing values to their occurrence counts,
                    typically from timing_histogram().
    """
    if not hist:
        print("Histogram is empty.")
        return
    
    print("Timing Value Histogram:")
    print("-" * 30)
    for timing_value, count in hist.items():
        print(f"{timing_value:8} us: {count:6} ")


def meanify_messages(messages, reduced_hist, tolerance_percentage):
    """
    Meanify the messages based on the reduced histogram.
    """
    meanified_messages = []
    for timings, freq in messages:  # Each message is a tuple of (frequency, timings)
        meanified_message = []
        for timing in timings:  # Each timing is a microsecond value
            found_similar = False
            for val in reduced_hist:  # Each value is a microsecond value
                if abs(timing - val) < (val*tolerance_percentage/100):
                    meanified_message.append(val)
                    found_similar = True
                    break
            if not found_similar:
                meanified_message.append(timing)
        meanified_messages.append((meanified_message, freq))
    return meanified_messages

def convert_to_binary(meanified_messages, start_bits, stop_bits):
    """
    Converts meanified messages to binary.
    """
    binary_messages = []
    for timings, freq in meanified_messages:
        binary_message = []
        for v1, v2 in zip(timings[::2], timings[1::2]):
            binary_message.append(1 if v1<v2 else 0)
        binary_messages.append(binary_message[start_bits:-stop_bits])

    return binary_messages

def convert_to_hex(binary_messages):
    """
    Converts binary messages to hex.
    """
    hex_messages = []
    for binary_message in binary_messages:
        hex_message = []
        for binary in binary_message:
            hex_message.append(binary)
        hex_messages.append(hex_message)
    return hex_messages

def chunks_forward(data, chunk_size):
    """Yields successive n-sized chunks from the list in forward order."""
    # Start index from the end of the list
    start = 0
    while start < len(data):
        # Calculate the end index for the slice, ensuring it doesn't go past the end of the list
        end = min(len(data), start + chunk_size)
        # Slice the chunk and yield
        # The slice data[start:end] gets the chunk in forward order
        yield data[start:end]
        # Move the start index forward
        start += chunk_size

def convert_to_hex(binary_message, lsbfirst=False, wordsize=4):
    """
    Converts a binary message to hex.
    """
    hex_message = []
    checksum = 0
    for chunk in chunks_forward(binary_message, wordsize):
        if len(chunk) != wordsize:
            chunk.extend([0] * (wordsize - len(chunk)))
        if lsbfirst:
            bin2dec = 0
            for i in range(wordsize):
                bin2dec += chunk[i] * (2 ** i)
            hexval = f"{bin2dec:02X}"    # convert to hex and pad with 0s
            hex_message.append(hexval)
            checksum += bin2dec
        else:
            bin2dec = 0
            for i in range(wordsize):
                bin2dec += chunk[i] * (2 ** (wordsize - i - 1))
            hexval = f"{bin2dec:02X}"    # convert to hex and pad with 0s
            hex_message.append(hexval)
            checksum += bin2dec
    checksum = checksum - bin2dec # 8 bit checksum
    checksum = checksum & 0xFF
    return hex_message, checksum

def print_binary_messages(binary_messages, start_offset=0, stride=1):
    """
    Prints binary messages in a readable format.
    """
    for i in range(start_offset, len(binary_messages), stride):
        binary_message = binary_messages[i]
        if i>=(start_offset+stride):
            old_binary_message = binary_messages[i-stride]
        else:
            old_binary_message = binary_message
        
        print(Fore.GREEN + f"Message {i}:\t" + Style.RESET_ALL, end="")
        s=0
        for (new, old) in zip(binary_message, old_binary_message):
            
            if s%4==0:
                print(f" ", end="")
            s+=1
            if new != old:
                print(Fore.RED + f"{new}"+ Style.RESET_ALL, end="") 
            else:
                print(f"{new}"+ Style.RESET_ALL, end="") 
        print(Fore.GREEN + f" Length: {len(binary_message)}" + Style.RESET_ALL)
    print(f"")
    return

