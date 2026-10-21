Point(1) = {-2, 0, 0, 0.1};
//+
Point(2) = {4, 0, 0, 0.1};
//+
Point(3) = {4, 2.5, 0, 0.1};
//+
Point(4) = {-2, 2.5, 0, 0.1};
//+
Point(5) = {0, 0.25, 0, 0.1};
//+
Point(6) = {1, 0.25, 0, 0.1};
//+
Point(7) = {1, 0.5, 0, 0.1};
//+
Point(8) = {0, 0.5, 0, 0.1};
//+
Line(1) = {1, 2};
//+
Line(2) = {2, 3};
//+
Line(3) = {3, 4};
//+
Line(4) = {4, 1};
//+
Line(5) = {5, 6};
//+
Line(6) = {6, 7};
//+
Line(7) = {7, 8};
//+
Line(8) = {8, 5};
//+
Curve Loop(1) = {1, 2, 3, 4};
//+
Curve Loop(2) = {5, 6, 7, 8};
//+
Plane Surface(1) = {1, 2};
//+
Rotate {{1, 0, 0}, {0, 0, 0}, -Pi/72} {
  Surface{1}; 
}
//+
Extrude {{1, 0, 0}, {0, 0, 0}, Pi/36} {
  Surface{1}; Layers{1}; Recombine;
}
//+

// Cylinder wall refinement
Field[1] = Box;
Field[1].VIn = 0.01;
Field[1].VOut = 0.1;
Field[1].XMin = -0.05;
Field[1].XMax = 1.05;
Field[1].YMin = 0.20;
Field[1].YMax = 0.55;
Field[1].ZMin = -0.1;
Field[1].ZMax = 0.1;

// Bow shock refinement
Field[2] = Box;
Field[2].VIn = 0.01;
Field[2].VOut = 0.1;
Field[2].XMin = -0.45;
Field[2].XMax = -0.05;
Field[2].YMin = 0.1;
Field[2].YMax = 1.0;
Field[2].ZMin = -0.1;
Field[2].ZMax = 0.1;

// Combine
Field[3] = Min;
Field[3].FieldsList = {1, 2};
Background Field = 3;

Mesh.MeshSizeFromPoints = 0;
Mesh.MeshSizeFromCurvature = 0;
Mesh.MeshSizeExtendFromBoundary = 0;

//+
Physical Volume(1) = {1};
//+
Physical Surface("inlet") = {28};
//+
Physical Surface("outlet") = {21};
//+
Physical Surface("farfield") = {25};
//+
Physical Surface("cylinderWalls") = {36, 32, 44, 40};
//+
Physical Surface("wedgeFront") = {45};
//+
Physical Surface("wedgeBack") = {1};
