import traceback
import adsk.core
import adsk.fusion

def run(_context: str):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        des = adsk.fusion.Design.cast(app.activeProduct)
        rootComp = des.rootComponent

        # Prompt the user to select a mesh body
        ui.messageBox('Click near the center of a triangle on a mesh body to create a sketch of that triangle.')
        selection = ui.selectEntity('Select a mesh body', 'MeshBodies')

        if not selection:
            return

        # Get the selected mesh body and the point where the user clicked
        meshBody = adsk.fusion.MeshBody.cast(selection.entity)
        clickPoint = selection.point

        if meshBody:
            # Get the display mesh data
            displayMesh = meshBody.displayMesh

            # Get the triangle indices from the display mesh
            triangleIndices = displayMesh.nodeIndices
            nodeCoordinates = displayMesh.nodeCoordinates

            minDistance = 99999999.0
            closestTriangleIndex = -1

            # Initialize progress bar
            progressBar = ui.progressBar
            progressBar.show('Counting triangles... %p%', 0, len(triangleIndices))
            updateIndexMod = int(len(triangleIndices) / 1000)

            # Iterate through all the triangles
            # triangleIndices stores the node indices for each triangle,
            # so we step through the array three at a time.
            for i in range(0, len(triangleIndices), 3):
                
                # Update progress bar every so often
                if i % updateIndexMod == 0:
                    progressBar.progressValue = i

                # Get the nodes that form the triangle
                node1 = nodeCoordinates[triangleIndices[i]]
                node2 = nodeCoordinates[triangleIndices[i+1]]
                node3 = nodeCoordinates[triangleIndices[i+2]]
                
                # Calculate the centroid of the triangle
                centroid = adsk.core.Point3D.create((node1.x + node2.x + node3.x) / 3.0,
                                                    (node1.y + node2.y + node3.y) / 3.0,
                                                    (node1.z + node2.z + node3.z) / 3.0)

                # Find the distance from the click point to the triangle centroid
                distance = clickPoint.distanceTo(centroid)
                if distance < minDistance:
                    minDistance = distance
                    closestTriangleIndex = i // 3

            progressBar.hide()

            if closestTriangleIndex != -1:
                # Get the coordinates
                p1 = nodeCoordinates[triangleIndices[closestTriangleIndex*3]]
                p2 = nodeCoordinates[triangleIndices[closestTriangleIndex*3+1]]
                p3 = nodeCoordinates[triangleIndices[closestTriangleIndex*3+2]]

                # Create sketch and points
                sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)
                sketch.name = f'[{closestTriangleIndex}] Triangle Sketch'

                sketchPoint1 = sketch.sketchPoints.add(p1)
                sketchPoint2 = sketch.sketchPoints.add(p2)
                sketchPoint3 = sketch.sketchPoints.add(p3)

                # Draw the lines to form the triangle
                sketchLines = sketch.sketchCurves.sketchLines
                sketchLines.addByTwoPoints(sketchPoint1, sketchPoint2)
                sketchLines.addByTwoPoints(sketchPoint2, sketchPoint3)
                sketchLines.addByTwoPoints(sketchPoint3, sketchPoint1)

                ui.messageBox(f'Sketch of triangle {closestTriangleIndex} successfully created')
            else:
                ui.messageBox('Could not find a triangle.')
    except:  #pylint:disable=bare-except
        if ui:
            ui.messageBox(f'Failed:\n{traceback.format_exc()}')
        if progressBar:
            progressBar.hide()
        app.log(f'Failed:\n{traceback.format_exc()}')
