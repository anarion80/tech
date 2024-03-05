# :jigsaw: TECH Controllers integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![Project Maintenance][maintenance-shield]][maintainer]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

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

## :warning: Disclaimer

Due to a stall on the original [mariusz-ostoja-swierczynski/tech-controllers](https://github.com/mariusz-ostoja-swierczynski/tech-controllers) repo, we have forked.
Most of the work was done by Mariusz Ostoja-Świerczyński, for which we're very thankful as the community.
It's time to move on, however. New formats of plugins appear, HA goes on with the feature implementation,
and as a community we need make sure that this plugin keeps up to the changing world. This repository also draws on work by [MichalKrasowski](https://github.com/MichalKrasowski), [micles123](https://github.com/micles123) and [nedyarrd](https://github.com/nedyarrd) - just putting it all together.

## :sparkles: Features

- Configuration through UI
- Support for multiple controllers which can be individually imported under given single account
- Provides Climate entities representing zones
  - and their corresponding Temperature, Battery, Humidity sensors when available
- Climate entities display data through Thermostat card
- Provides sensors for eModul 'tiles'
- Automatic naming and translations of tiles from eModul API

**This integration will set up the following platforms.**

Platform | Description
-- | --
`binary_sensor` | Show info and status from Tech API.
`sensor` | Show info and status from Tech API.
`climate` | Thermostats.

![Tech Thermostat Cards](/custom_components/tech/images/ha-tech-1.png)

## ✏ Plans for development

- Publish the tech.py Python Package to PyPI
- Write tests for HA component
- Support for window opening sensor
- Support for cold tolerance setting
- Support for zones schedules
- Services for pumps, operating mode changes, etc

## 🏗 Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `tech`.
1. Download _all_ the files from the `custom_components/tech/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Tech Controllers"
1. Enter your username (could be email) and password for your eModule account and click "Submit" button.
1. In the next step select the controllers you want to import/integrate
1. You should see "Success!" dialog with the name of the imported controller(s).
1. Now you should have Climate entities representing your home zones available in Home Assistant. Go to your UI Lovelace configuration and add Thermostat card with your Climate entities.

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

***

[buymecoffee]: https://www.buymeacoffee.com/anarion
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/custom-components/blueprint.svg?style=for-the-badge
[commits]: https://github.com/anarion80/tech/commits/main
[license-shield]: https://img.shields.io/github/license/anarion80/tech?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-anarion80-blue.svg?style=for-the-badge
[maintainer]: https://github.com/anarion80
[releases-shield]: https://img.shields.io/github/release/anarion80/tech.svg?style=for-the-badge
[releases]: https://github.com/anarion80/tech/releases
