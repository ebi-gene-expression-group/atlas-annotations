download_file() {
  local URL=$1
  local OUTPUT_FILE=$2

  local STATUS=$(curl -L -s --write-out "%{http_code}" -o $OUTPUT_FILE "$URL")
  if [ $STATUS -ne 200 ]; then
    echo "ERROR retrieiving file from $URL, got HTTP Code $STATUS"
    echo "See $OUTPUT_FILE content."
    exit 1
  fi
}
