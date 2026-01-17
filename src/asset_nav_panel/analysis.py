import uuid
import maya.cmds as cmds
import maya.api.OpenMaya as om


#Open it not in an Maya viwe port
def gather_mesh_stats(shape):
    sel = om.MSelectionList()
    sel.add(shape)
    dag = sel.getDagPath(0)
    mesh = om.MFnMesh(dag)

    ngons = 0
    for i in range(mesh.numPolygons):
        if len(mesh.getPolygonVertices(i)) > 4:
            ngons += 1

    return {
        "vertices": mesh.numVertices,
        "polygons": mesh.numPolygons,
        "ngons": ngons,
        "uv_sets": mesh.getUVSetNames(),
    }


def analyze_model(model_path):
    """
    Safely imports a model into a temporary namespace,
    gathers mesh statistics, then cleans up.
    """
    original_scene = cmds.file(q=True, sn=True)
    
    report = {
        "model": model_path,
        "meshes": [],
        "errors": []
    }

    try:
        cmds.file(new=True, force=True)
        cmds.file(model_path, i=True,  ignoreVersion=True)

        meshes = cmds.ls(type="mesh")
        print(len(meshes))
        if not meshes:
            report["errors"].append("No mesh found")

        for m in meshes:
            try:
                stats = gather_mesh_stats(m)
                stats["mesh"] = m
                report["meshes"].append(stats)
            except Exception as e:
                report["errors"].append(str(e))

    except Exception as e:
        report["errors"].append(str(e))

    finally:
        # Restore original scene
        if original_scene:
            cmds.file(original_scene, open=True, force=True)
        else:
            cmds.file(new=True, force=True)


    return report
