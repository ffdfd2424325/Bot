{ pkgs ? import <nixpkgs> {} }:

pkgs.buildPythonApplication {
  pname = "telegram-bot";
  version = "1.0";
  src = ./.;

  propagatedBuildInputs = with pkgs.python311Packages; [
    aiogram
    python-dotenv
    apscheduler
  ];

  meta = with pkgs.lib; {
    description = "Telegram bot application";
    license = licenses.mit;
  };
}
