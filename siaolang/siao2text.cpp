#include <iostream>
#include <string>
#include <vector>

std::string hex2utf8(const std::string& hexString) {
  std::string utf8String;
  std::string byteString;

  for (size_t i = 0; i < hexString.length(); i += 2) {
    byteString = hexString.substr(i, 2);  // Extract two characters
    char byte = static_cast<char>(
        std::stoi(byteString, nullptr, 16));  // Convert hex to byte
    utf8String += byte;
  }

  return utf8String;
}

std::vector<std::string> split_string(const std::string& s, char seperator) {
  std::vector<std::string> output;

  std::string::size_type prev_pos = 0, pos = 0;

  while ((pos = s.find(seperator, pos)) != std::string::npos) {
    std::string substring(s.substr(prev_pos, pos - prev_pos));

    output.push_back(substring);

    prev_pos = ++pos;
  }

  output.push_back(s.substr(prev_pos, pos - prev_pos));  // Last word

  return output;
}

std::string siao2text(const std::string& siao_text) {
  auto words = split_string(siao_text, ' ');

  std::vector<char> original_chars;
  for (const std::string& word : words) {
    int n_siao = 0;
    int i = 0;

    while (i < word.length()) {
      if (word[i] == 's') {
        n_siao += 1;
        i += 4;
      } else if (word[i] == 'm') {
        n_siao += 4;
        i += 3;
      } else if (word[i] == 'l') {
        n_siao += 9;
        i += 3;
      } else if (word[i] == 'a') {
        n_siao += 19;
        i += 7;
      } else {
        exit(EXIT_FAILURE);
      }
    }

    char c;
    if (n_siao > 10) {
      c = n_siao - 10 + 'a';
    } else {
      c = n_siao + '0';
    }
    original_chars.push_back(c);
  }

  std::string original_str(original_chars.begin(), original_chars.end());
  return hex2utf8(original_str);
}

int main(int argc, char** argv) {
  if (argc < 2) {
    std::cout << "Usage: " << argv[0] << " \"<siao_text>\"" << std::endl;
    exit(EXIT_FAILURE);
  }

  auto siao_text = argv[1];
  std::string original_text = siao2text(siao_text);
  std::cout << original_text << std::endl;

  return 0;
}
