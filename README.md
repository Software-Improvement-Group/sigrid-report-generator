# Report generator

## Intro

The SIG report generator is a tool/framework designed to generate any kind of report. The repo only contains one (default) template, but it should be capable of producing others in the future, of different export types. Additionally, at some point it could be integrated into Sigrid, so that end-users can download a report/export at the click of a button.

<img src="./docs/img/sample-mgmt-summary.png" alt="Sample: Management summary" width="300px">
<img src="./docs/img/sample-architecture.png" alt="Sample: Architecture" width="300px">
<img src="./docs/img/sample-test-code.png" alt="Sample: Test code ratio" width="300px">
<img src="./docs/img/sample-word.png" alt="Sample: Word" width="300px">

## Status

This tool is currently in the proof-of-concept phase. Things may not completely work yet, or break at a given time. Usage is at your own risk. Please contact the team working on the tool if you have an urgent need, but that there is no official support at this moment.

## Installation

See [docs/installation.md](docs/installation.md)

## Usage

### Create customer-specific access token

Before using the system, you need to generate a Sigrid token. Tokens are unique **per customer**. Create a new token for a new customer:

1. Go to Sigrid: `https://sigrid-says.com/<your-customer>`
2. Go to user settings, via the person icon on the top right
3. Click "create new token" and create a token with a descriptive name, e.g. `customername-report-generator`.
4. Save the token somewhere so you don't need to recreate it every time. (Tokens are valid for 1 year)

### Run the tool

1. For the default report, use: `report-generator -c <your-customer> -s <your-system> -t <your-sigrid-token>`
2. If you want to provide your own custom report `.pptx` or `.docx` file. Use: `report-generator -p <your-file.pptx> -c <your-customer> -s <your-system> -t <your-sigrid-token>`
3. For help or an overview of all options use `report-generator --help`

If all goes well, the report should be generated into `out.pptx`/`out.docx` in the folder where you run the command, or wherever you specify with the `-o` option.  

#### Troubleshooting

If there is an error and you can't figure out what causes it, run the tool again with the `-d` parameter appended to gather additional information. Then (for now) consult the team behind the tool (@jan / @dobrien) and send them the output.

Use `report-generator --help` for an overview of configuration options.

## Create your own template

Report generator is flexible. It allows you to input your own `.pptx` or `.docx` template, and it will populate it with data from Sigrid. You can define your template from scratch, or modify an existing template. You can find the built-in templates in the `src/report_generator/templates` folder of the report-generator repository. Once you have created your template, you can insert it into the reourt generator by using the `-p`/`--template` command line argument.

There are roughly two types of items in a template that report-generator deals with:

- **Textual data**: Data such as numbers and text can be freely placed wherever you want it. In a table, in a paragraph, in a slide title. This works with placeholders. For example, if you write `MAINT_RATING` in your template, the tool will replace that with the actual maintainability rating. A large number of metrics/texts is supported. For a full overview, see [docs/placeholder descriptions.md](docs/placeholder%20descriptions.md)
- **Charts**: These are not yet very flexible. You can change the look and feel of the charts define in the existing templates, but you cannot change their structure. If you think a chart with a different structure is clearly needed, or better than the current visualization, reach out to the report-generator team. At the time of writing, only several PowerPoint charts are supported.

## Suggestions / feedback

Feedback is welcome! If you have ideas to improve report-generator, please reach out to the team. Currently @jan manages this process. If you want to do him a favor, create a ticket in this project, but a Slack message also works. Merge requests are also welcome! Potential improvent areas include:

- Improved standard templates;
- Request for more Sigrid data exposed through the tool;
- Bug fixes;
- Future usecases of this tool;
- Easier deployment suggestions or other technical improvements;
- ...

## Help developing

For instructions specific to developers, see [docs/developers.md](docs/developers.md)

## License

Copyright Software Improvement Group

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.