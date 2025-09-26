import struct

input_file = "random_numbers.txt"
output_file = "random_numbers.bin"

with open(input_file, 'r') as infile, open(output_file, 'wb') as outfile:
    for line in infile:
        try:
            # Converte cada linha (número) para um inteiro de 32 bits e salva como binário
            num = int(line.strip())
            outfile.write(struct.pack('<I', num))
        except (ValueError, struct.error) as e:
            print(f"Erro ao converter a linha '{line.strip()}': {e}")

print(f"Conversão concluída. Arquivo binário salvo como '{output_file}'.")
