# :warning: Disclaimer

Due to a stall on the original [mariusz-ostoja-swierczynski/tech-controllers](https://github.com/mariusz-ostoja-swierczynski/tech-controllers) repo, we have forked.
Most of the work was done by Mariusz Ostoja-Świerczyński, for which we're very thankful as the community.
It's time to move on, however. New formats of plugins appear, HA goes on with the feature implementation,
and as a community we need make sure that this plugin keeps up to the changing world. This repository also draws on work by [MichalKrasowski](https://github.com/MichalKrasowski), [micles123](https://github.com/micles123) and [nedyarrd](https://github.com/nedyarrd) - just putting it all together.

## :jigsaw: TECH Controllers integration for Home Assistant

This is an integration of heating controllers from Polish company TECH Sterowniki Sp. z o.o. It uses API to their web control application eModul.eu, therefore your controller needs to be accessible from the Internet and you need an account either on <https://emodul.eu> or <https://emodul.pl>.

The integration is based on API provided by TECH which supports the following controllers:

- L-4 Wifi
- L-7
- L-8
- WiFi 8S
- ST-8S WiFi

The integration was developed and tested against eModul demo account (username: `test`/password: `test`) which features 4 controllers:

- I-3
- L-8
- Pellet
- Solar

Additionally, I own M-9r so that is also tested.
Everything else might or might not work - needs community help, testing and reporting back what works.

The integration is in no way supported or endorsed by TECH Sterowniki sp. z o.o.

## :sparkles: Features

- Configuration through UI
- Support for multiple controllers which can be individually imported under given single account
- Provides Climate entities representing zones
  - and their corresponding Temperature, Battery, Humidity sensors when available
- Climate entities display data through Thermostat card
- Provides sensors for eModul 'tiles'
- Automatic naming and translations of tiles from eModul API

![Tech Thermostat Cards](/custom_components/tech/images/ha-tech-1.png)

## ✏ Plans for development

- Publish the tech.py Python Package to PyPI
- Write tests for HA component
- Support for window opening sensor
- Support for cold tolerance setting
- Support for zones schedules
- Services for pumps, operating mode changes, etc

## 🏗 Installation

1. Copy entire repository content into your `config/custom_components/tech` folder of your Home Assistant installation.
   **Note:** If you don't have `custom_components` folder you need to create it first and create `tech` folder in it.
2. Restart Home Assistant.
3. Go to Configuration -> Integrations and click Add button.
4. Search for "Tech Controllers" integration and select it.
5. Enter your username (could be email) and password for your eModule account and click "Submit" button.
6. In the next step select the controllers you want to import/integrate
7. You should see "Success!" dialog with the name of the imported controller(s).
8. Now you should have Climate entities representing your home zones available in Home Assistant. Go to your UI Lovelace configuration and add Thermostat card with your Climate entities.

![Tech Controllers Setup 1](/custom_components/tech/images/ha-tech-add-integration-1.png)

![Tech Controllers Setup 2](/custom_components/tech/images/ha-tech-add-integration-2.png)

![Tech Controllers Setup 3](/custom_components/tech/images/ha-tech-add-integration-3.png)

![Tech Controllers Setup 3](/custom_components/tech/images/ha-tech-add-integration-4.png)

![Tech Controllers Setup 4](/custom_components/tech/images/ha-tech-2.png)

## 🚀 List of reported working TECH Controllers

- L4-WiFi (v.1.0.24)
- L-7 (v.2.0.8)
- L-7E (v.1.0.6)
- L-8 (v.3.0.14)
- L-9r (v1.0.2)
- WiFi 8S (v.2.1.8)
- ST-8s WIFI (v.1.0.5)
- ST-16s WIFI (v.1.0.5)
- M-9 (v1.0.12)
- M-9r (v1.3.8)

## 📝 Copyright & License

Copyright (c) 2024 anarion80 - Released under the [MIT](LICENSE) license.
