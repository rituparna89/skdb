import unittest, math
from skdb.geom import *
from skdb import load_package, Package, close_enough

#for test_shape_volume
from OCC.BRepAlgoAPI import *
from OCC.BRepPrimAPI import *
from OCC.gp import *

def point_trsf(point1, transformation):
    '''point_trsf(point1, transformation) -> [x,y,z]'''
    point1 = Point(point1)
    result_pnt = point1.Transformed(transformation)
    return result_pnt

class TestGeom(unittest.TestCase):
    def init_interface(self):
        foo = Interface(name='foo', point=(1,1,1), orientation=[2,2,2], rotation=0)
        return foo
    def test_interface(self):
        '''this really probably shouldnt go here, but if interface screws up then so will everything else'''
        self.init_interface()
    def init_part(self):
        foo = self.init_interface()
        part = Part(name='unitcube') #, file='../pymates/models/block-with-hole.step')#too big, want 2x2x2
        #self.part.load_CAD()
        part.interfaces.append(foo)
        return part
    def test_part(self):
        '''ditto'''
        part = self.init_part()
    def test_point(self):
        point = Point(1,2,3)
        point = Point(0,0,0)
        point = Point([1,2,3])
        point = Point((1,2,3))
        point = Point(gp_Pnt(1,2,3))
        point = Point(Point(1,2,3))
        point = Point(Vector(1,2,3))
        point = Point(gp_Vec(1,2,3))
    def test_point_eq(self):
        self.assertEqual(geom.Point(0,0,0), geom.Point(0,0,0))
        self.assertEqual(geom.Point(0,0,1e-9), geom.Point(0,0,0))
        #not equals?
    def test_point_transformed_no_side_effects(self):
        '''Point.transformed should return a new Point'''
        point = Point(1,2,3)
        point2 = point.transformed(gp_Trsf())
        self.assertFalse(point2 is point) 
    def test_point_yaml(self):
        import yaml
        self.assertEqual(yaml.dump(geom.Point(0, 0, 0.00000001)), "!point ['0.0', '0.0', 1e-08]\n")
        self.assertEqual(yaml.dump(geom.Point(0, 0, 0.000000000000001)), "!point ['0.0', '0.0', '0.0']\n")
        self.assertEqual(yaml.load("!point ['0.0', '0.0', 1e-08]"), geom.Point(0, 0, 0.00000001))
        self.assertEqual(yaml.load("!point [0.0, 0.0, 1e-08]"), geom.Point(0, 0, 0.00000001))    
        self.assertEqual(yaml.dump(geom.Point(0,0,1e-8)), "!point ['0.0', '0.0', 1e-08]\n")
    def test_vec(self):
        vec = Vector(1,2,3)
        vec = Vector([1,2,3])
    def test_vec_eq(self):                                                                         
        self.assertEqual(geom.Vector(0,0,0), geom.Vector(0,0,0))
        self.assertEqual(geom.Vector(0,0,1e-9), geom.Vector(0,0,0)) 
        #not equals? 
    def test_vec_yaml(self):
        import yaml
        self.assertEqual(yaml.dump(geom.Vector(0, 0, 0.00000001)), "!vector ['0.0', '0.0', 1e-08]\n")
        self.assertEqual(yaml.load("!vector ['0.0', '0.0', 1e-08]"), geom.Vector(0, 0, 0.00000001))
    def test_dir(self): #maybe we can just force everyone to use !vector instead of !orientation or !direction (it's the same thing)
        dir = Direction(1,2,3)
    def test_build_trsf(self):
        a = build_trsf([0,0,0], [1,0,0], [0,1,0])
        self.assertEqual(a.TranslationPart().Coord(), (0,0,0))
        #print Point(Point(1,2,3).Transformed(a)), Point(1,2,3)
        self.assertEqual(Point(1,2,3).Transformed(a), Point(1,2,3))
        self.assertTrue(Direction(1,1,0).Angle(Direction(1,1,math.sqrt(2)))/(math.pi/180) - 45 < 1e-10)


    def test_transformation(self):
        '''note: gp_Trsf not be stored in yaml'''
        trans0 = geom.Transformation()
        point1 = Point(1,2,3)
        point2 = Point(4,5,6)
        trans1 = trans0.SetTranslation(point1, point2)
        point3 = Point(10,10,15)
        trans2 = trans1.SetTranslation(point2, point3)
        
        #make sure it keeps the tree/stacking information correctly
        self.assertTrue(trans0.get_children()==[trans1, [trans2]])

        point4 = Point(15,5,2)
        new_point = point4.transformed(trans2)
        
        #make sure it put the point in the correct spot
        expected_point = Point(21,10,11)
        self.assertTrue(new_point == expected_point)
        
    def test_stacked_transformations(self):
        transformation0 = geom.Transformation()
        transformation1 = transformation0.SetTranslation(Point(0,0,0), Point(0,0,1))
        transformation2 = transformation1.SetTranslation(Point(0,5,0), Point(1,2,0))
        transformation3 = transformation2.run() #stacking
        new_point = Point(0,0,0).transformed(transformation3)
        self.assertEqual(new_point, Point(1,-3,0))

    def test_shape_volume(self):
        box1 = BRepPrimAPI_MakeBox(gp_Pnt(0,0,0), gp_Pnt(10,10,10))
        box2 = BRepPrimAPI_MakeBox(gp_Pnt(0,0,0), gp_Pnt(10,10,10))
        fuse = BRepAlgoAPI_Fuse(box1.Shape(), box2.Shape())
        fused_shape = fuse.Shape()

        from skdb.geom import shape_volume
        box1_volume = shape_volume(box1.Shape())
        box2_volume = shape_volume(box2.Shape())
        fused_volume = shape_volume(fused_shape)

        self.assertEqual(box1_volume, box2_volume)
        self.assertEqual(box1_volume, fused_volume)

        #change box size
        box2 = BRepPrimAPI_MakeBox(gp_Pnt(5,5,5), gp_Pnt(10,10,10))
        fuse = BRepAlgoAPI_Fuse(box1.Shape(), box2.Shape())
        fused_shape = fuse.Shape()
        box2_volume = shape_volume(box2.Shape())
        fused_volume = shape_volume(fused_shape)
        self.assertTrue(close_enough(box1_volume/8, box2_volume))
        #self.assertTrue(close_enough(box2_volume, fused_volume)) #fused_volume should be 1000

        #now move the other box over a bit
        box2 = BRepPrimAPI_MakeBox(gp_Pnt(10,10,10), gp_Pnt(20,20,20))
        fuse = BRepAlgoAPI_Fuse(box1.Shape(), box2.Shape())
        fused_shape = fuse.Shape()
        box2_volume = shape_volume(box2.Shape())
        fused_volume = shape_volume(fused_shape)
        self.assertTrue(close_enough(fused_volume/2, box1_volume))
        #fused_volume = 2000

    def test_boundingbox(self):
        len_x, len_y, len_z = 10, 11, 12
        box_shape = BRepPrimAPI_MakeBox(Point(0,0,0), Point(len_x, len_y, len_z)).Shape()
        box = BoundingBox(shape=box_shape)
        #max on x, y, z should be len_x, len_y, len_z .. especially for a box.
        #OCC adds Precision().Confusion() to the box on purpose
        self.assertTrue(close_enough(box.x_max, len_x))
        self.assertTrue(close_enough(box.y_max, len_y))
        self.assertTrue(close_enough(box.z_max, len_z))
        
        #this could get filled out more but who cares
        self.assertTrue(box.contains(gp_Pnt(len_x, len_y, len_z)))
        
        #what about a more complicated shape?
        how_about_not_right_now='''
        pack = Package("lego")
        brick1 = deepcopy(pack.parts[0])
        box2 = BoundingBox(shape=brick1.shapes[0])
        print box2
        #for brick_thick_round.stp, you should get something like:
        #BoundingBox(x=[-15.6, 0.0], y=[0.0, 11.3284], z=[-14.0176443928, -1.58235560717])
        #was verified in heekscad
        self.assertTrue(box2.x_max == 0)
        self.assertTrue(box2.y_min == 0)
        self.assertTrue(box2.x_min < 0)
        self.assertTrue(box2.y_max > 11.3)
        self.assertTrue(box2.z_min < -14)
        self.assertTrue(box2.z_max < -1)'''
    def test_boundingbox_collision(self):
        '''this where the fun begins :-)'''
        len_x, len_y, len_z = 10, 11, 12
        box_shape = BRepPrimAPI_MakeBox(Point(0,0,0), Point(len_x, len_y, len_z)).Shape()
        box = BoundingBox(shape=box_shape)

        box_shape2 = BRepPrimAPI_MakeBox(Point(0,0,0), Point(len_x, len_y, len_z)).Shape()
        box2 = BoundingBox(shape=box_shape2)
        self.assertTrue(box.interferes(box2))

        box_shape3 = BRepPrimAPI_MakeBox(Point(5,5,5), Point(len_x, len_y, len_z)).Shape()
        box3 = BoundingBox(shape=box_shape3)
        self.assertTrue(box.interferes(box3))
    def test_face(self):
        occ_shape = BRepPrimAPI_MakeBox(Point(0,0,0), Point(1,1,1)).Shape()
        #assume the shape is just a single face
        face = Face(occ_shape)
        self.assertTrue(len(face.points)>0)

if __name__ == "__main__":
    unittest.main()
