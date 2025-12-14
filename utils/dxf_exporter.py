import ezdxf
import traceback
import numpy as np

def export_bspline_to_dxf(bspline_processor, chord_length_mm, logger_func):
    """
    Export B-spline curves to DXF as NURBS curves.
    
    Args:
        bspline_processor: BSplineProcessor instance with fitted B-spline data
        chord_length_mm (float): The desired chord length in millimeters for scaling
        logger_func (callable): A function to send log messages to
        
    Returns:
        ezdxf.document.Drawing: The created DXF document object, or None if an error occurred
    """
    try:
        if not bspline_processor.fitted:
            logger_func("Error: No B-spline fit available for DXF export.")
            return None
            
        if chord_length_mm <= 0:
            logger_func("Error: Chord length must be positive for DXF export.")
            return None

        logger_func(f"Preparing B-spline DXF export with chord length: {chord_length_mm:.2f} mm...")

        # Get B-spline control points and knot vectors
        upper_ctrl_pts = bspline_processor.upper_control_points
        lower_ctrl_pts = bspline_processor.lower_control_points
        upper_knots = bspline_processor.upper_knot_vector
        lower_knots = bspline_processor.lower_knot_vector
        
        if upper_ctrl_pts is None or lower_ctrl_pts is None:
            logger_func("Error: B-spline control points not available for DXF export.")
            return None
        
        if upper_knots is None or lower_knots is None:
            logger_func("Error: B-spline knot vectors not available for DXF export.")
            return None
        
        # Scale control points by chord length
        upper_ctrl_pts_scaled = upper_ctrl_pts * chord_length_mm
        lower_ctrl_pts_scaled = lower_ctrl_pts * chord_length_mm
        
        # Create DXF document
        doc = ezdxf.new('R2000')
        doc.header["$INSUNITS"] = 4  # millimeters
        msp = doc.modelspace()
        
        # Convert control points to format expected by ezdxf
        upper_points = [tuple(pt.tolist()) for pt in upper_ctrl_pts_scaled]
        lower_points = [tuple(pt.tolist()) for pt in lower_ctrl_pts_scaled]
        
        # Convert knot vectors to lists (ezdxf expects a list)
        upper_knots_list = upper_knots.tolist()
        lower_knots_list = lower_knots.tolist()
        
        # Get degree from the processor - use fitted_degree if available (actual degree used during fitting),
        # otherwise fall back to degree (which may have been restored to config value)
        degree = bspline_processor.fitted_degree if bspline_processor.fitted_degree is not None else bspline_processor.degree
        
        logger_func(f"Creating NURBS curves: degree {degree} ({'from fitted B-spline' if bspline_processor.fitted_degree is not None else 'from config'})")
        logger_func(f"  Upper knot vector: {len(upper_knots_list)} knots")
        logger_func(f"  Lower knot vector: {len(lower_knots_list)} knots")
        
        # Create SPLINE entities directly with control points and knots
        # Using add_open_spline which accepts control_points, degree, and knots
        upper_spline = msp.add_open_spline(
            control_points=upper_points,
            degree=degree,
            knots=upper_knots_list
        )
        upper_spline.dxf.layer = "AIRFOIL_UPPER"
        upper_spline.dxf.color = 1  # Red
        logger_func(f"  Upper surface: degree {degree} B-spline with {len(upper_points)} control points")
        
        # Add lower surface NURBS curve  
        lower_spline = msp.add_open_spline(
            control_points=lower_points,
            degree=degree,
            knots=lower_knots_list
        )
        lower_spline.dxf.layer = "AIRFOIL_LOWER"
        lower_spline.dxf.color = 5  # Blue
        logger_func(f"  Lower surface: degree {degree} B-spline with {len(lower_points)} control points")
        
        # Add trailing edge connector if needed (for blunt trailing edge)
        if not bspline_processor.is_sharp_te:
            if not np.allclose(upper_ctrl_pts_scaled[-1], lower_ctrl_pts_scaled[-1]):
                msp.add_line(
                    tuple(upper_ctrl_pts_scaled[-1].tolist()), 
                    tuple(lower_ctrl_pts_scaled[-1].tolist()),
                    dxfattribs={'layer': 'TRAILING_EDGE_CONNECTOR', 'color': 2}  # Yellow
                )
                logger_func("  Added trailing edge connector for blunt trailing edge")
        
        logger_func(f"B-spline DXF export completed successfully.")
        return doc
        
    except Exception as e:
        logger_func(f"Error during B-spline DXF export: {e}")
        logger_func(traceback.format_exc())
        return None
