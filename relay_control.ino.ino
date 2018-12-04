/* 8 Relay Module configured for Opto-isolation
   Arduino UNO pins 3 to 10 connected to IN1 to IN8
   Connections: http://i.imgur.com/MDNQGeC.png */

void setup() {
  for (int i = 0; i <= 5; i++) {
    pinMode(i, INPUT_PULLUP);
    pinMode(i, OUTPUT); // defaults HIGH (relays off)
  }
}

void loop() {
  for (int i = 0; i <= 5; i++) {
    digitalWrite(i, LOW); // energize relays until all on
    delay(1000);
  }
  for (int i = 0; i <= 5; i++) {
    digitalWrite(i, HIGH); // de-energize relays until all off
    delay(1000);
  }
}
