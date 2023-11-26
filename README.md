# Blender Named Selection Add-on

## Introduction
The Blender Named Selection Add-on allows you to create a named selection for one or more selected objects directly from the viewport.  

## Key Benefit
Objects in a named selection can be quickly selected with a single button click.

## Installation
To install the Named Selection Add-on in Blender, follow these steps:
1. Download the `NamedSelection.py` file from this repository.
2. Open Blender and go to `Edit > Preferences > Add-ons`.
3. Click `Install` and navigate to the downloaded `.py` file.
4. Select the file and click `Install Add-on`.
5. Enable the add-on by ticking the checkbox next to its name.

## Usage
Once installed, the add-on can be accessed in the 3D Viewport under the sidebar (press `N` to toggle). 

### Interface
![User interface](imagedocumentation/example.png "This is an example image")

In the Named Selection interface, all added named selections are displayed.

The buttons below the named selection list let's you create and remove named selections, select objects in a named selection, add or remove objects from it, remove all objects in a named selection, add or remove objects from a named selection and rename the named selection.

### Creating a Named Selection
1. Select the objects you want to group in the 3D Viewport.
2. Go to the Named Selections tab in the sidebar.
3. Click `Add` and enter a name for the selection.

### Managing Named Selections
- **View List**: All named selections are listed in the Named Selections tab.
- **Select Objects**: Click `Select` to select all objects in a named selection.
- **Add/Remove Objects**: Select objects and use `Add Objects` or `Remove Object` to modify a named selection.
- **Rename**: Click `Rename` to change a named selection's name.
- **Clear**: Use `Clear Named Selection` to empty a selection without deleting it.
- **Remove**: Delete a named selection with the `Remove` button.

## Features
- Create and manage named selections of objects.
- Easily add, remove, and select objects within named selections.
- View all named selections in a user-friendly list.
- Automatically updates selections when objects are deleted.
- Intuitive UI integrated seamlessly into Blender's interface.

## Contributing
Contributions to the Named Selection Add-on are welcome. To contribute:
1. Fork the repository.
2. Create a new branch for your feature.
3. Commit your changes.
4. Push to the branch.
5. Submit a pull request.

## License
This project is licensed under [GPLv3](LICENSE). See the LICENSE file for more details.

## Contact
For support, feedback, or inquiries, please contact [KCRWorld] at [kcreative@kcrworld.com].
