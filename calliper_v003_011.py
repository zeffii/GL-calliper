import bpy
import bgl
import blf
import bpy_extras
from math import pi, degrees, floor

from mathutils import Vector, Euler
from bpy.props import StringProperty, FloatProperty, BoolProperty
from bpy_extras.view3d_utils import location_3d_to_region_2d as loc3d2d

'''
GPL2 License applies. Code by Dealga McArdle. Use at own risk.

Script for measuring the distance between two selected empties. In addition
to measuring the linear distance, also delta x,y and z are given.

Axis mode displays axis lines using an openGL overlay
Dimensions mode will display (at a later stage) the dimensions lines as per 
engineering conventions.

Script also displays the angular spread of 3 selected empties.

[todo]  make real
[todo]  store set


'''

# temporary constants
DEBUG = 0
NUM_UNITS = 2   # describes the distance of the dimension line in world space 
TRIANGLE_SIZE = 0.5 # some idea about the world size of the triangle
TRIANGLE_SIZE_FACTOR = 1.0 # scale factor
TRIANGLE_SIZE = TRIANGLE_SIZE * TRIANGLE_SIZE_FACTOR
# DISPLAY_TOLERANCE = 5e-4 # not suitable for engineering.
ANG_ROUND = 6
DEG_ROUND = 6
FLIP_DISTANCE = 18  # distance in px, flip markers to outside if below


'''
    helper functions 
'''

def get_objects(context):
    sel_obs = context.selected_objects        
    names = [object.name for object in sel_obs if object.type=='EMPTY']
    if len(names) in (2,3): 
        return names
    else: 
        return None
    

def get_distance(names_of_empties):
    if names_of_empties == None:
        return 0.0

    coordlist = []
    for name in names_of_empties:
        coordlist.append(bpy.data.objects[name].location)

    return (coordlist[0]-coordlist[1]).length


def get_distance_from_context(context):
    distance = get_distance(get_objects(context))
    return distance


def get_coordinates_from_empties(object_list):
    coordlist = [obj.location for obj in object_list]
    return coordlist


def get_difference(axis, coord):
    if axis == 'z':
        return abs((coord[0]-coord[1]).z)
    elif axis == 'y':
        return abs((coord[0]-coord[1]).y)
    elif axis == 'x':
        return abs((coord[0]-coord[1]).x)
    else:
        return None


def return_sorted_coordlist(coords):
    def MyFn(coord):  
        return coord.z
    return sorted(coords, key=MyFn, reverse=True)
            

# simple coordinate retrieving.
def get_tetrahedron(clist):
    apex, baseco = return_sorted_coordlist(clist)
    base1 = Vector((apex.x, apex.y, baseco.z))
    base2 = Vector((apex.x, baseco.y, baseco.z))
    base3 = baseco
    return apex, base1, base2, base3    


'''
    openGL drawing
'''


def draw_text(col, y_pos, display_text, view_width, context):

    # calculate text width, then draw
    font_id = 0
    blf.size(font_id, 18, 72)  #fine tune
    
    text_width, text_height = blf.dimensions(font_id, display_text)
    right_align = view_width-text_width-18
    blf.position(font_id, right_align, y_pos, 0)
    blf.draw(font_id, display_text)
    return

def draw_linear_line(region, rv3d, context, coordinate_list):
   
    # 50% alpha, 2 pixel width line
    bgl.glEnable(bgl.GL_BLEND)
    
    bgl.glColor4f(0.7, 0.7, 0.7, 0.5)
    bgl.glLineWidth(1)
    
    bgl.glBegin(bgl.GL_LINE_STRIP)
    for coord in coordinate_list:
        vector3d = (coord.x, coord.y, coord.z)
        vector2d = loc3d2d(region, rv3d, vector3d)
        bgl.glVertex2f(*vector2d)
    bgl.glEnd()



def draw_tetrahedron(region, rv3d, context, tetra_coords):
    apex, base1, base2, base3 = tetra_coords

    # converting to screen coordinates
    screen_apex = loc3d2d(region, rv3d, apex)
    screen_base1 = loc3d2d(region, rv3d, base1) 
    screen_base2 = loc3d2d(region, rv3d, base2)
    screen_base3 = loc3d2d(region, rv3d, base3)
    
    # colour + line setup, 50% alpha, 1 px width line
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glLineWidth(1)
        

    # linear distance line
    bgl.glColor4f(0.6, 0.6, 0.6, 0.8)
    bgl.glBegin(bgl.GL_LINES)
    bgl.glVertex2f(*screen_apex)  
    bgl.glVertex2f(*screen_base3)  
    bgl.glEnd()

    # x
    bgl.glColor4f(1.0, 0.1, 0.1, 0.8)
    bgl.glBegin(bgl.GL_LINES)  
    bgl.glVertex2f(*screen_base3)  
    bgl.glVertex2f(*screen_base2)
    bgl.glEnd()

    # y
    bgl.glColor4f(0.0, 1.0, 0.1, 0.8)    
    bgl.glBegin(bgl.GL_LINES)  
    bgl.glVertex2f(*screen_base2)
    bgl.glVertex2f(*screen_base1)  
    bgl.glEnd()

    # z
    bgl.glColor4f(0.1, 0.3, 1.0, 0.8)
    bgl.glBegin(bgl.GL_LINES)  
    bgl.glVertex2f(*screen_apex)  
    bgl.glVertex2f(*screen_base1)  
    bgl.glEnd()

    # distraction line 1 & 2  
    bgl.glColor4f(0.3, 0.3, 0.3, 0.6)
    bgl.glLineStipple(4, 0x5555) 
    bgl.glEnable(bgl.GL_LINE_STIPPLE) 

    bgl.glBegin(bgl.GL_LINES)  
    bgl.glVertex2f(*screen_apex)  
    bgl.glVertex2f(*screen_base2)  
    bgl.glVertex2f(*screen_base1)  
    bgl.glVertex2f(*screen_base3)  
    bgl.glEnd()

    # done    
    bgl.glDisable(bgl.GL_LINE_STIPPLE)
    bgl.glEnable(bgl.GL_BLEND)  # back to uninterupted lines
    
    # quick and dirty while developing
    


def draw_dimensions(region, rv3d, context, tetra_coords):
    
    
    apex, base1, base2, base3 = tetra_coords

    # TODO WARNING FACTORABLE CODE AHEAD
    # converting to screen coordinates
    screen_apex = loc3d2d(region, rv3d, apex)
    screen_base1 = loc3d2d(region, rv3d, base1) 
    screen_base2 = loc3d2d(region, rv3d, base2)
    screen_base3 = loc3d2d(region, rv3d, base3)
    
    # DRAW X  
    if base3.y > apex.y:
        YDIR = 1 
    else:
        YDIR = -1 
    # do we need to draw at all if there is no x distance?        
    if base3.y != apex.y:
        y_dir = NUM_UNITS * YDIR
        base3_ext_y = Vector((base3.x, base3.y+y_dir, base3.z))
        base2_ext_y = Vector((base2.x, base2.y+y_dir, base2.z))
        scr_base3_ext_y = loc3d2d(region, rv3d, base3_ext_y)
        scr_base2_ext_y = loc3d2d(region, rv3d, base2_ext_y)
        
        bgl.glColor4f(0.203, 0.8, 1.0, 0.8)
        bgl.glBegin(bgl.GL_LINES)
        bgl.glVertex2f(*screen_base3)  
        bgl.glVertex2f(*scr_base3_ext_y)  
        bgl.glVertex2f(*screen_base2)  
        bgl.glVertex2f(*scr_base2_ext_y)  
        bgl.glEnd()

    # DRAW Y
    if base3.x > apex.x:
        XDIR = -1 
    else:
        XDIR = 1 
    # do we need to draw at all if there is no y distance?        
    if base3.x != apex.x:    
        x_dir = NUM_UNITS * XDIR
        base2_ext_x = Vector((base2.x+x_dir, base2.y, base2.z))
        base1_ext_x = Vector((base1.x+x_dir, base1.y, base1.z))
        scr_base2_ext_x = loc3d2d(region, rv3d, base2_ext_x)
        scr_base1_ext_x = loc3d2d(region, rv3d, base1_ext_x)
        
        bgl.glColor4f(0.203, 0.8, 1.0, 0.8)
        bgl.glBegin(bgl.GL_LINES)
        bgl.glVertex2f(*screen_base2)  
        bgl.glVertex2f(*scr_base2_ext_x)  
        bgl.glVertex2f(*screen_base1)  
        bgl.glVertex2f(*scr_base1_ext_x)  
        bgl.glEnd()
 
    # DRAW Z 
    # check if there is a z distance
    if apex.z != base3.z:
        # draw z, use oposite y direction
        y_dir = NUM_UNITS * -YDIR
        apex_ext_y = Vector((apex.x, apex.y+y_dir, apex.z))
        base1_ext_y = Vector((base1.x, base1.y+y_dir, base1.z))
        scr_apex_ext_y = loc3d2d(region, rv3d, apex_ext_y)
        scr_base1_ext_y = loc3d2d(region, rv3d, base1_ext_y)
        
        bgl.glColor4f(0.203, 0.8, 1.0, 0.8)
        bgl.glBegin(bgl.GL_LINES)
        bgl.glVertex2f(*screen_apex)  
        bgl.glVertex2f(*scr_apex_ext_y)  
        bgl.glVertex2f(*screen_base1)  
        bgl.glVertex2f(*scr_base1_ext_y)  
        bgl.glEnd()

    

    # DRAW LINEAR
    # necessarily at the end because we know the y direction now.
    
    # X/Y angle (between base1, base3, base2)
    # find a cleaner (more clever) way to do 
    if (apex.x > base3.x) and (apex.y > base3.y):
        vec1 = base1-base3
        vec2 = base2-base3
        XY_RAD = vec1.angle(vec2) # -(pi*0.75)    
    elif (apex.x > base3.x) and (apex.y < base3.y):
        vec1 = base2-base1
        vec2 = base3-base1
        XY_RAD = vec1.angle(vec2)+(1.5*pi)    
    elif (apex.y > base3.y) and (apex.x < base3.x):
        vec1 = base2-base1
        vec2 = base3-base1
        XY_RAD = vec1.angle(vec2)-(0.5*pi)    
    elif (apex.x < base3.x) and (apex.y < base3.y):
        vec1 = base2-base1
        vec2 = base3-base1
        XY_RAD = -vec1.angle(vec2) +(0.5*pi)
    elif apex.y == base3.y:
        XY_RAD = pi
    elif apex.x == base3.x:
        XY_RAD = 0.5*pi
    else: 
        # dont bother drawing it.
        return
    

    # what a jungle.
    marker_xyz = Vector((0.0, NUM_UNITS*-YDIR, 0.0))
    myEul = Euler((0.0, 0.0, XY_RAD), 'XYZ')
    marker_xyz.rotate(myEul)    # rotate and modify vector in place.
    
    apex_ext_xyz = apex + marker_xyz
    base3_ext_xyz = base3 + marker_xyz
    
    scr_apex_ext_xyz = loc3d2d(region, rv3d, apex_ext_xyz)
    scr_base3_ext_xyz = loc3d2d(region, rv3d, base3_ext_xyz)
    
    bgl.glColor4f(0.203, 0.8, 1.0, 0.8)
    bgl.glBegin(bgl.GL_LINES)
    bgl.glVertex2f(*screen_base3)  
    bgl.glVertex2f(*scr_base3_ext_xyz)  
    bgl.glVertex2f(*screen_apex)  
    bgl.glVertex2f(*scr_apex_ext_xyz)  
    bgl.glEnd()
        
    #print("drawing dimensions next")
    return



def draw_tris(region, rv3d, context):
    divs = 24   # verts per fan.
    n = 3       # ratio of shortest edge.

    def get_tri_coords(object_list):
        # replace for empties code.
        coordlist = [obj.location for obj in object_list]
        return coordlist
    
    def get_angle_rad(set_of_coords):
        coord1, coord2, coord3 = set_of_coords
        angle_rad = (coord1-coord2).angle(coord3-coord2)
        angle_deg = degrees(angle_rad)
        return angle_rad, angle_deg
    
    
    # if 3 empties selected
    coord1, coord2, coord3 = get_tri_coords(context.selected_objects)
    
    # measure angle between 
    angle1 = [coord3, coord1, coord2]
    angle2 = [coord1, coord2, coord3]
    angle3 = [coord2, coord3, coord1]
        
    edge1 = (coord1-coord2).length
    edge2 = (coord2-coord3).length
    edge3 = (coord3-coord1).length
    shortest_edge = min(edge1, edge2, edge3)
    radial_d = shortest_edge / n
    
    
    
    def make_fan_poly_from_edges(angle_object, radius):
        coordinate_1, shared_co, coordinate_2 = angle_object
    
        # get length of edge, lerp it , place a point at radial distance (pointN)
        len1 = (coordinate_1-shared_co).length
        len2 = (coordinate_2-shared_co).length
        tlerp1 = 1/(len1/radius)
        tlerp2 = 1/(len2/radius)
        point1 = shared_co.lerp(coordinate_1, tlerp1)
        point2 = shared_co.lerp(coordinate_2, tlerp2)
                
        # place imaginary line between (point1, point2)
        radial_collection = []
        radial_collection.append(shared_co)
      
        # start from point1, place temp point (1/24)*i   
        # collect points. check all points for distance to angle_point.
        rate = 1/divs
        for notch in range(divs+1):
            new_vec = point1.lerp(point2, rate*notch)
            # move new vec away from shared point until the distance is radius.
            new_vec_len = (new_vec-shared_co).length
            lerp_distance = radius/new_vec_len
            radial_point = shared_co.lerp(new_vec, lerp_distance)
            radial_collection.append(radial_point)
        
        radial_collection.append(shared_co)
              
        # make polygon 
        return radial_collection
       
    
    bgl.glEnable(bgl.GL_BLEND) # enable blending
    bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)
    
    angle_list = [angle1, angle2, angle3]
    for item in angle_list:
        polyline = make_fan_poly_from_edges(item, radial_d)
    
        #can be modified per polyline    
        bgl.glColor4f(0.103, 0.3, 0.6, 0.4)    
    
        bgl.glBegin(bgl.GL_POLYGON)    
        for segment in polyline:
            scr_pixel = loc3d2d(region, rv3d, segment)
            bgl.glVertex2f(*scr_pixel)  
    
        bgl.glEnd()
        

    # get text.        
    for item in angle_list:    

        bgl.glColor4f(0.83, 0.8, 0.9, 0.7)    
        angrad, angdeg = get_angle_rad(item)
        polyline = make_fan_poly_from_edges(item, radial_d)

        # find coordinate to place the text
        cpoint1 = polyline[0]
        midpoint = floor(len(polyline)/2)
        cpoint2 = polyline[midpoint]
        cmidway = cpoint1.lerp(cpoint2, 0.5)
        scr_coord = loc3d2d(region, rv3d, cmidway)
        
        # round both text
        angrad_round = round(angrad, ANG_ROUND)
        angdeg_round = round(angdeg, DEG_ROUND)
        str_angrad = str(angrad_round)
        str_angdeg = str(angdeg_round)
        combined_string = str_angrad + " , " + str_angdeg
        
        
        # get length of text, place text .5 of length to the left of the coord.
        font_id = 0
        blf.size(font_id, 12, 72)  
        
        text_width, text_height = blf.dimensions(font_id, combined_string)
        x_pos = text_width/2

        blf.position(font_id, scr_coord[0]-x_pos, scr_coord[1], 0)
        blf.draw(font_id, combined_string)
        
    return




def draw_callback_px(self, context):
    rounding = 6
    
    objlist = context.selected_objects
    names_of_empties = [i.name for i in objlist]

    region = context.region
    rv3d = context.space_data.region_3d
    view_width = region.width

    # draw line    
    if len(names_of_empties) == 2:
        
        distance_value = get_distance(names_of_empties)
        coordinate_list = get_coordinates_from_empties(objlist)
        
        # major rewrite candidate
        l_distance = str(round(distance_value, rounding))
        x_distance = round(get_difference('x', coordinate_list),rounding)
        y_distance = round(get_difference('y', coordinate_list),rounding)
        z_distance = round(get_difference('z', coordinate_list),rounding)
        l_distance = str(l_distance)+" lin"
        x_distance = str(x_distance)+" x"
        y_distance = str(y_distance)+" y"            
        z_distance = str(z_distance)+" z"
        
        y_heights = 88, 68, 48, 20
        y_heights = [m-9 for m in y_heights]  # fine tune
        
        str_dist = x_distance, y_distance, z_distance, l_distance
        for i in range(len(y_heights)):
            draw_text(True, y_heights[i], str_dist[i], view_width, context)
        
        # get coordinates and draw.
        tetra_coords = get_tetrahedron(coordinate_list)
        draw_linear_line(region, rv3d, context, coordinate_list)    
        
        if  context.scene.DrawAxisSwitch == True:
            draw_tetrahedron(region, rv3d, context, tetra_coords)
    
        if  context.scene.DrawDimensions == True:
            draw_dimensions(region, rv3d, context, tetra_coords)

    #draw tri
    if len(names_of_empties) == 3:
        print("time to draw tris!")        
        draw_tris(region, rv3d, context)


    
    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)

    return









'''
    tool panel and button definitions
'''


class ToolPropsPanel(bpy.types.Panel):
    bl_label = "Empties Calliper"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    
    scn = bpy.types.Scene
    ctx = bpy.context

    scn.DrawAxisSwitch = BoolProperty(default=False, name="Axis")
    scn.DrawDimensions = BoolProperty(default=False, name="Dimensions")


    @classmethod
    def poll(self, context):
        names_of_empties = get_objects(context)
        if names_of_empties != None:
            return True

    def draw(self, context):

        display_distance_field = False
        
        layout = self.layout
        scn = context.scene

        names_of_empties = get_objects(context)
        
        if len(names_of_empties) == 2:
            
            button_str = names_of_empties[0] + "  -->  " +  names_of_empties[1]
                    
            display_distance_field = True
            distance_value = get_distance(names_of_empties)
            dist_val = str(distance_value)
            
            # drawing        
            row1 = layout.row(align=True)
            row1.label(button_str)
            
            row2 = layout.row(align=True)
            row2.prop(scn, "DrawAxisSwitch")
            row2.prop(scn, "DrawDimensions")
    
            row3 = layout.row(align=True)
            row3.operator("hello.hello", text="Draw to viewport").switch = True
            row3.operator("hello.hello", text="Cancel").switch= False
    
            if display_distance_field == True:
                row4 = layout.row(align=True)
                row4.label(dist_val)
                row5 = layout.row(align=True)
                row5.operator("distance.copy", text="copy to clipboard").d_val = dist_val
    

        if len(names_of_empties) == 3:

            row1 = layout.row(align=True)
            row2 = layout.row(align=True)
            row3 = layout.row(align=True)
            row1.label("1 ) "+str(names_of_empties[0]))
            row2.label("2 ) "+str(names_of_empties[1]))
            row3.label("3 ) "+str(names_of_empties[2]))
            row4 = layout.row(align=True)
            row4.operator("tri.drawing", text="Draw angles")


class OBJECT_OT_DrawAngles(bpy.types.Operator):
    bl_idname = "tri.drawing"
    bl_label = "Draw angles"

    def modal(self, context, event):
        context.area.tag_redraw()
        
        # TODO: READ UP, this is not so intuitive.
        if event.type == 'MIDDLEMOUSE':
            # context.area.tag_redraw()
            print(event.value) 
            if event.value == 'PRESS':
                print("Allow to rotate")
                context.area.tag_redraw()
                return {'PASS_THROUGH'}           
            if event.value == 'RELEASE':
                context.area.tag_redraw()
                print("allow to interact with ui")
                return {'PASS_THROUGH'}
     
        
        if event.type in ('WHEELUPMOUSE', 'WHEELDOWNMOUSE'):
            context.area.tag_redraw()
            return {'PASS_THROUGH'}   
        
        if event.type == 'RIGHTMOUSE':
            if event.value == 'RELEASE':
                print("discontinue drawing")
                context.area.tag_redraw()
                context.region.callback_remove(self._handle)
                return {'CANCELLED'}  
         
        
        return {'PASS_THROUGH'}    

    def invoke(self, context, event):


        if context.area.type == 'VIEW_3D':
            context.area.tag_redraw()
            context.window_manager.modal_handler_add(self)

            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self._handle = context.region.callback_add(
                            draw_callback_px, 
                            (self, context), 
                            'POST_PIXEL')

            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, 
            "View3D not found, cannot run operator")
            context.area.tag_redraw()            
            return {'CANCELLED'}



class OBJECT_OT_CopyButton(bpy.types.Operator):
    bl_idname = "distance.copy"
    bl_label = "copy to clipboard"
    
    d_val = bpy.props.StringProperty()
    
    def execute(self, context):  
        bpy.data.window_managers[0].clipboard = self.d_val
        return{'FINISHED'}


class OBJECT_OT_HelloButton(bpy.types.Operator):
    bl_idname = "hello.hello"
    bl_label = "Say Hello"

    switch = bpy.props.BoolProperty()
    
    def modal(self, context, event):  
        context.area.tag_redraw()  
        
        # TODO: READ UP, this is not so intuitive.
        if event.type == 'MIDDLEMOUSE':
            # context.area.tag_redraw()
            print(event.value) 
            if event.value == 'PRESS':
                print("Allow to rotate")
                context.area.tag_redraw()
                            
            if event.value == 'RELEASE':
                context.area.tag_redraw()
                print("allow to interact with ui")

            return {'PASS_THROUGH'}      
        
        if event.type in ('WHEELUPMOUSE', 'WHEELDOWNMOUSE'):
            context.area.tag_redraw()
            return {'PASS_THROUGH'}          
        
        elif event.type == 'RIGHTMOUSE':
            if event.value == 'RELEASE':
                print("discontinue drawing")
                context.area.tag_redraw()
                context.region.callback_remove(self._handle)
                return {'CANCELLED'}  
            
        if event.type == 'LEFTMOUSE':
            if event.value == 'CLICK':
                context.area.tag_redraw()
                return {'PASS_THROUGH'}        
     
        return {'RUNNING_MODAL'}  
     
    def invoke(self, context, event):

        if self.switch == True:
            if context.area.type == 'VIEW_3D':
                context.area.tag_redraw()
                context.window_manager.modal_handler_add(self)
    
                # Add the region OpenGL drawing callback
                # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
                self._handle = context.region.callback_add(
                                draw_callback_px, 
                                (self, context), 
                                'POST_PIXEL')
    
                return {'RUNNING_MODAL'}
            else:
                self.report({'WARNING'}, 
                "View3D not found, cannot run operator")
                
                return {'CANCELLED'}

        if self.switch == False:
            context.area.tag_redraw()
            # context.region.callback_remove(self._handle)
            print("done")
            return {'FINISHED'}        

    

bpy.utils.register_module(__name__)
