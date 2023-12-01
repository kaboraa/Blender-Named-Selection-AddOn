bl_info = {
    "name": "Named Selections",
    "description": "Create and manage named selections of objects in the Blender scene.",
    "author": "Kwaku Oteng Aboraa",
    "version": (1, 0, 1),
    "blender": (2, 93, 0),
    "location": "View3D > Sidebar > Named Selections Panel",
    "warning": "",  # used for warning icon and text in addons panel
    "wiki_url": "https://github.com/kaboraa/Blender-Named-Selection-AddOn",
    "category": "Object"
}

# Constants
GITHUB_USER = "kaboraa"
GITHUB_REPO = "Blender-Named-Selection-AddOn"
CURRENT_VERSION = "v1.0.1"  # Update this as needed

import os
import addon_utils
import bpy
import threading
import requests
from bpy.props import StringProperty, CollectionProperty
from bpy.types import Operator, Panel, PropertyGroup

bpy.types.Scene.show_named_selection_info = bpy.props.BoolProperty(
    name="Show Info",
    description="Show additional information about the Named Selection addon",
    default=False
)

bpy.types.Scene.show_release_note = bpy.props.BoolProperty(
    name="Show Release Notes",
    description="Show release information",
    default=True
)


# Define a simple property to store the update message
def get_addon_prefs():
    user_preferences = bpy.context.preferences
    return user_preferences.addons[__name__].preferences

def register_properties():
    """Registers custom properties used by the addon.

    This includes properties for update messages and showing release notes.
    """
    bpy.types.WindowManager.update_check_message = bpy.props.StringProperty(
        name="Update Check Message",
        default="Current version: " + CURRENT_VERSION
    )


def unregister_properties():
    del bpy.types.WindowManager.update_check_message
 
class CheckForUpdateOperator(bpy.types.Operator):
    """Operator to check for updates to the addon from GitHub.

    This operator checks the specified GitHub repository for the latest release version
    and compares it with the current version of the addon.
    """
    bl_idname = "wm.check_for_update"
    bl_label = "Check for Update"

    def execute(self, context):
        # Set the initial message
        context.window_manager.update_check_message = "Checking for updates..."
        # Run the version check in a new thread to avoid blocking the Blender UI
        thread = threading.Thread(target=self.check_for_update, args=(context,))
        thread.start()
        return {'FINISHED'}

    def check_for_update(self, context):
        try:
            latest_version = self.get_latest_release(GITHUB_USER, GITHUB_REPO)
            current_version = CURRENT_VERSION
            # Prepare the message
            if latest_version is None:
                message = "Could not check for updates. Please try again later."
            elif latest_version == current_version:
                message = "You are using the latest version."
            else:
                message = f"Update available! Latest version: {latest_version}"

            # Update the message property
            context.window_manager.update_check_message = message
            
        except Exception as e:
            message = f"Failed to check for updates: {str(e)}"
            context.window_manager.update_check_message = message

    def get_latest_release(self, user, repo):
        url = f"https://api.github.com/repos/{user}/{repo}/releases/latest"
        response = requests.get(url)
        if response.ok:
            return response.json()['tag_name']
        else:
            return None  
        
# A custom property group that stores the name and objects of a named selection
class NamedSelection(PropertyGroup):
    """
    Custom property group for storing details of a named selection.

    This class represents a named selection, holding a name for the selection
    and a collection of objects that are part of this selection. It is used
    to manage groups of objects under a user-defined name within the Blender scene.

    Attributes:
        name (StringProperty): The name assigned to the named selection.
        objects (CollectionProperty): A collection of objects included in the named selection.
    """
    
    name: StringProperty(name="Name", default="Unnamed") # The name of the named selection
    objects: CollectionProperty(type=bpy.types.PropertyGroup) # The objects in the named selection

# A custom operator that adds a new named selection from the selected objects
class AddNamedSelection(Operator):
    """Operator to add a new named selection.

    Creates a new named selection from the currently selected objects in the Blender scene.
    Allows naming the selection for future reference.
    """
    
    bl_idname = "object.add_named_selection"
    bl_label = "Add Named Selection"
    bl_description = "Add a new named selection from the selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty(name="Name", default="Unnamed") # The name of the new named selection

    def execute(self, context):
        # Get the scene
        scene = context.scene
        
        # Create a new named selection and add it to the scene's custom property
        named_selection = scene.named_selections.add()
        named_selection.name = self.name

        # Add the selected objects to the named selection's custom property
        # This will add objects if there are any selected, otherwise the named selection will be empty
        for obj in context.selected_objects:
            named_selection.objects.add().name = obj.name

        # Update the listbox index to show the new named selection
        bpy.types.UIList.active_index = len(scene.named_selections) - 1
        
        # Set the newly added named selection as the active one
        scene = context.scene
        scene.named_selections_index = len(scene.named_selections) - 1
        
        # Force a UI refresh
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return {'FINISHED'}
    
    def generate_unique_name(self, scene):
        base_name = "Unnamed"
        existing_names = {ns.name for ns in scene.named_selections}
        
        if base_name not in existing_names:
            return base_name

        # Increment the suffix until an unused name is found
        counter = 1
        while f"{base_name}.{str(counter).zfill(2)}" in existing_names:
            counter += 1

        return f"{base_name}.{str(counter).zfill(2)}"

    def invoke(self, context, event):
        # Show a dialog to enter the name of the new named selection
        scene = context.scene
        self.name = self.generate_unique_name(scene)
        return context.window_manager.invoke_props_dialog(self)

# A custom operator that selects the objects in a named selection
class SelectNamedSelection(Operator):
    """Operator to select objects from a named selection.

    Selects all objects that are part of a specific named selection in the scene.
    Supports appending to the current selection.
    """
    
    bl_idname = "object.select_named_selection"
    bl_label = "Select Named Selection"
    bl_description = "Select the objects in the named selection. Hold SHIFT to append to current selection."
    bl_options = {'REGISTER', 'UNDO'}
    
    append: bpy.props.BoolProperty()  # Add a property to store the append state
    
    @classmethod
    def poll(cls, context):
        return context.scene.named_selections

    def invoke(self, context, event):
        # The invoke function is called when the operator is called
        # Here we set the append property based on the Shift key state
        self.append = event.shift
        return self.execute(context)

    def execute(self, context):
        # Get the scene and the active named selection
        scene = context.scene
        named_selection = scene.named_selections[scene.named_selections_index]

        # Check if we should append to the current selection
        if not self.append:
            # Deselect all objects if not appending
            bpy.ops.object.select_all(action='DESELECT')


       # Select the objects in the named selection
        for obj in named_selection.objects:
            object = bpy.data.objects.get(obj.name)
            if object:
                object.select_set(True)
                
       # Make sure the active object is set to one of the selected objects
        if named_selection.objects and not self.append:
            bpy.context.view_layer.objects.active = bpy.data.objects[named_selection.objects[0].name]

        return {'FINISHED'}
# A custom operator that removes a named selection
class RemoveNamedSelection(Operator):
    """Operator to remove an existing named selection.

    Removes a named selection from the scene. This action does not delete the objects,
    only the grouping reference.
    """
    
    bl_idname = "object.remove_named_selection"
    bl_label = "Remove Named Selection"
    bl_description = "Remove the named selection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        # Get the index of the currently active named selection
        active_idx = scene.named_selections_index

        # Check if the index is valid
        if active_idx < 0 or active_idx >= len(scene.named_selections):
            self.report({'WARNING'}, "No valid named selection selected")
            return {'CANCELLED'}

        # Remove the active named selection
        scene.named_selections.remove(active_idx)

        # Update the active index to a valid value
        if active_idx >= len(scene.named_selections):
            scene.named_selections_index = len(scene.named_selections) - 1
        else:
            scene.named_selections_index = active_idx

        # Force a UI refresh
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return {'FINISHED'}

# A custom operator that removes an object from a named selection
class RemoveObjectFromNamedSelection(Operator):
    """
    Operator to remove the active object from a named selection.

    This operator allows users to remove the currently active object from a specified named selection.
    It modifies the named selection to exclude the active object, updating the collection of objects
    within that selection. The operation is registered for undo/redo capabilities in Blender.

    """
    bl_idname = "object.remove_object_from_named_selection"
    bl_label = "Remove Object From Named Selection"
    bl_description = "Remove the active object from the named selection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Get the scene, the active object and the active named selection
        scene = context.scene
        named_selection_index = scene.named_selections_index
        
        
        named_selection = scene.named_selections[named_selection_index]
        
         # Iterate over all selected objects and add them if they are not already in the named selection
        for obj in context.selected_objects:
            if obj.name in [o.name for o in named_selection.objects]:
                 # Find the index of the object in the named selection's custom property
                index = named_selection.objects.find(obj.name)
                # Remove the object from the named selection's custom property
                named_selection.objects.remove(index)      

        return {'FINISHED'}

# A custom operator that adds an object to a named selection
class AddObjectToNamedSelection(Operator):
    bl_idname = "object.add_object_to_named_selection"
    bl_label = "Add Object To Named Selection"
    bl_description = "Add the active object to the named selection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        named_selection_index = scene.named_selections_index

        # Ensure there is a valid named selection
        if named_selection_index >= len(scene.named_selections):
            self.report({'WARNING'}, "No named selection selected")
            return {'CANCELLED'}

        named_selection = scene.named_selections[named_selection_index]

        # Iterate over all selected objects and add them if they are not already in the named selection
        for obj in context.selected_objects:
            if obj.name not in [o.name for o in named_selection.objects]:
                named_selection.objects.add().name = obj.name

        return {'FINISHED'}


class ClearNamedSelection(Operator):
    bl_idname = "object.clear_named_selection"
    bl_label = "Clear Named Selection"
    bl_description = "Clear all objects from the named selection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        named_selection_index = scene.named_selections_index

        # Ensure there is a valid named selection
        if named_selection_index >= len(scene.named_selections):
            self.report({'WARNING'}, "No named selection selected")
            return {'CANCELLED'}

        named_selection = scene.named_selections[named_selection_index]
        
        # Clear all objects from the named selection
        named_selection.objects.clear()

        return {'FINISHED'}
    
class RenameNamedSelection(Operator):
    bl_idname = "object.rename_named_selection"
    bl_label = "Rename Named Selection"
    bl_description = "Rename the selected named selection"
    bl_options = {'REGISTER', 'UNDO'}

    new_name: bpy.props.StringProperty(name="New Name")

    def execute(self, context):
        scene = context.scene
        named_selection_index = scene.named_selections_index

        # Ensure there is a valid named selection
        if named_selection_index >= len(scene.named_selections):
            self.report({'WARNING'}, "No named selection selected")
            return {'CANCELLED'}

        # Rename the named selection
        named_selection = scene.named_selections[named_selection_index]
        named_selection.name = self.new_name
        
         # Force a UI refresh
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


        return {'FINISHED'}

    def invoke(self, context, event):
        named_selection_index = context.scene.named_selections_index
        if named_selection_index < len(context.scene.named_selections):
            self.new_name = context.scene.named_selections[named_selection_index].name
        return context.window_manager.invoke_props_dialog(self)


class NamedSelectionsPanel(Panel):
    """UI Panel for managing named selections.

    Provides a user interface in the Blender sidebar for managing named selections. 
    Includes options to create, remove, and interact with named selections.
    """
    
    bl_idname = "OBJECT_PT_named_selections"
    bl_label = "Named Selections"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        scene = context.scene
        
        # Collapsible info section
        col = layout.column()
        box = col.box()
        row = box.row()

        # This creates a clickable label that toggles the property
        # When clicked, it will expand or collapse the box below it
        row.prop(scene, "show_named_selection_info", icon="TRIA_DOWN" if scene.show_named_selection_info else "TRIA_RIGHT", emboss=False)
         # Display the update status message
  
        if scene.show_named_selection_info:
            # Expanded section with buttons
            expand_col = box.column(align=True)
            expand_col.label(text=wm.update_check_message)
            expand_col.operator("wm.check_for_update")          
      
            # Button to show release notes
            expand_col.operator("wm.url_open", text="Show Release Notes", icon='INFO').url = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/releases/tag/{CURRENT_VERSION}"
            # Documentation button
            expand_col.operator("wm.url_open", text="Documentation", icon='INFO').url = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}"          
            
            # Tutorial button
            tutorial_url = "https://www.youtube.com/"  # Replace with your actual tutorial link
            if tutorial_url and tutorial_url != "https://www.youtube.com/":
                expand_col.operator("wm.url_open", text="Tutorial", icon='FILE_MOVIE').url = tutorial_url
        
        # Check if the current mode is Object Mode
        is_object_mode = context.mode == 'OBJECT'

        row = layout.row(align=True)

        # Add column
        add_col = row.column(align=True)
        add_col.operator("object.add_named_selection", text="Add", icon='ADD')    
       
        # Remove column
        remove_col = row.column(align=True)
        remove_col.enabled = len(scene.named_selections) > 0
        remove_col.operator("object.remove_named_selection", text="Remove", icon='REMOVE')

        # Draw the listbox for showing the named selections
        layout.template_list("UI_UL_list", "named_selections", scene, "named_selections", scene, "named_selections_index")

        # Separate row for Select button with conditional enabling
        select_row = layout.row(align=True)
        select_row.scale_y = 1.5  # Increase the height of the button
        select_row.enabled = len(scene.named_selections) > 0 and is_object_mode
        select_row.operator("object.select_named_selection", text="Select Objects", icon='OBJECT_DATAMODE')        
      
 
        # Column for adding an object from a named selection with conditional enabling
        add_object_row = layout.row(align=True)
        active_object = context.active_object
        # Check if there is an active object and if it is selected
        add_object_row.enabled = len(scene.named_selections) > 0 and active_object and active_object.select_get()
        add_object_row.operator("object.add_object_to_named_selection", text="Add Objects", icon='ADD')

        # Column for removing an object from a named selection with conditional enabling
        remove_object_row = layout.row(align=True)
        named_selection_index = scene.named_selections_index
        active_object = context.active_object       

        # Check if the active object is selected and part of the current named selection
        if (named_selection_index < len(scene.named_selections) and
            active_object and active_object.select_get()):
            named_selection = scene.named_selections[named_selection_index]
            remove_object_row.enabled = active_object.name in [obj.name for obj in named_selection.objects]
        else:
            remove_object_row.enabled = False

        remove_object_row.operator("object.remove_object_from_named_selection", text="Remove Objects", icon='CANCEL')
        
        # Row for the Clear Named Selection button with conditional enabling
        clear_row = layout.row(align=True)
        clear_row.enabled = len(scene.named_selections) > 0 #and len(scene.named_selections[scene.named_selections_index].objects) > 0)
        clear_row.operator("object.clear_named_selection", text="Remove All Objects", icon='X')
         
         # Row for Rename button with conditional enabling
        rename_row = layout.row(align=True)
        rename_row.enabled = len(scene.named_selections) > 0
        rename_row.operator("object.rename_named_selection", text="Rename", icon='TOOL_SETTINGS')
        


# A handler function that updates the named selections when an object is deleted
def update_named_selections(scene):
    # Loop through all named selections in the scene
    for named_selection in scene.named_selections:
        # Loop through all objects in the named selection
        for obj in named_selection.objects:
            # Check if the object still exists
            if not bpy.data.objects.get(obj.name):
                # Find the index of the object in the named selection's custom property
                index = named_selection.objects.find(obj.name)

                # Remove the object from the named selection's custom property
                named_selection.objects.remove(index)

# Register the custom property group, operators, panel and handler
def register():
    register_properties()
    bpy.utils.register_class(CheckForUpdateOperator)
    bpy.utils.register_class(NamedSelection)
    bpy.utils.register_class(AddNamedSelection)
    bpy.utils.register_class(SelectNamedSelection)
    bpy.utils.register_class(RemoveNamedSelection)
    bpy.utils.register_class(RemoveObjectFromNamedSelection)
    bpy.utils.register_class(AddObjectToNamedSelection)
    bpy.utils.register_class(ClearNamedSelection)    
    bpy.utils.register_class(RenameNamedSelection)  
    bpy.utils.register_class(NamedSelectionsPanel)
    bpy.types.Scene.named_selections = CollectionProperty(type=NamedSelection)
    bpy.types.Scene.named_selections_index = bpy.props.IntProperty()
    bpy.app.handlers.depsgraph_update_post.append(update_named_selections)

# Unregister the custom property group, operators, panel and handler
def unregister():
    unregister_properties()
    bpy.utils.unregister_class(CheckForUpdateOperator)
    bpy.utils.unregister_class(NamedSelection)
    bpy.utils.unregister_class(AddNamedSelection)
    bpy.utils.unregister_class(SelectNamedSelection)
    bpy.utils.unregister_class(RemoveNamedSelection)
    bpy.utils.unregister_class(RemoveObjectFromNamedSelection)
    bpy.utils.unregister_class(AddObjectToNamedSelection)
    bpy.utils.unregister_class(ClearNamedSelection)
    bpy.utils.unregister_class(RenameNamedSelection)
    bpy.utils.unregister_class(NamedSelectionsPanel)
    del bpy.types.Scene.named_selections
    del bpy.types.Scene.named_selections_index
    bpy.app.handlers.depsgraph_update_post.remove(update_named_selections)

# Run the register function
if __name__ == "__main__":
    register()
