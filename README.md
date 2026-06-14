<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://github.com/fraktlfx/prism-slack/blob/main/Resources/prism_slack_logo_long_light_banner.png">
  <source media="(prefers-color-scheme: light)" srcset="https://github.com/fraktlfx/prism-slack/blob/main/Resources/prism_slack_logo_long_dark_banner.png">
  <img alt="Prism and Slack branding" src="https://github.com/fraktlfx/prism-slack/blob/main/Resources/prism_slack_logo_long_light_banner.png">
</picture>  
  
<div>
<img src="https://img.shields.io/badge/Prism_Pipeline-2.1.0-mediumseagreen" alt="Prism Pipeline Version"> 
<img src="https://img.shields.io/badge/Slack_Plugin-2.1.0-4A154B?logo=slack" alt="Slack Plugin Version">
</div>  
<br>
  
> [!IMPORTANT]  
> Most up to date docs can be found here: [FRAKTL Slack Plugin Documentation](https://docs.fraktlfx.com/prism/slack/home)
  
    
## Table of Contents  
1. [Introduction](#introduction)
2. [Requirements](#requirements)
    1. [Slack](#requirements-slack)
3. [Installation](#installation)
    1. [Prism - Install Plugin](#plugin)

## Introduction

This is the Community Edition of the Slack plugin for Prism-Pipeline 2.

> [!NOTE]
> If you are looking for the Studio Edition you can go here: [Fraktl Prism/Slack Studio Edition](https://fraktlfx.com/pipeline/prism-slack)

## Requirements

### Slack

1. Slack Bot

   - You are required to create a bot application in Slack. You can find the installation process for this below or check the documentation here: [Slack Bot Installation](https://docs.fraktlfx.com/prism/slack/installation)

2. Channel Name = Project Name
   - Your channel must match the name of your current project. If it doesn't, you will need to put it in the Custom Channel field in the project settings

## Installation

### CLI

For a shorter method of install the plugin, see the two commands below. Open a Terminal in your Prism Plugin directory and copy/paste/type in these commands:

> git clone https://github.com/fraktlfx/prism-slack.git Slack

    pip install -r requirements.txt -t ./PythonLibs

### Plugin

If you want to avoid the next 4 steps below, you can open a terminal in the Prism Plugins directory and run this command

> git clone https://github.com/fraktlfx/prism-slack.git Slack

1. Download the Plugin

> Option 1: Download the current release package from the repository's release page.

    Option 2: Download the repository as a ZIP file using the Code dropdown menu on the main repository page.

2.Unzip the File (if needed)

> If you downloaded the ZIP file, extract its contents to a folder.

3.Move the Plugin to the Prism Plugin Folder

    > Locate your Prism Plugin folder.

        Drag and drop the downloaded or unzipped plugin folder into the Prism Plugin folder.

4.Install Python Dependencies

   To reduce distribution size, the Python dependencies are not bundled directly with the plugin. You will need to run the following:
   - Windows
      - install_packages.bat

   - Mac/Linux
      - install_packages.sh

5.Start/Reload Prism

   - Restart Prism or reload plugins
   - Verify that the Slack plugin appears in the plugin list and is enabled

## Documentation & Support
  
All configuration steps, advanced usage, and troubleshooting are documented here:
  
https://docs.fraktlfx.com/prism/slack/home  
  
For any further questions please contact **Fraktl** directly at: support@fraktlfx.com