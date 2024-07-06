import React from "react";
import { Grid } from "@mui/material";

const GridContainer = React.forwardRef(
    (props, ref) => {
        return (
            <Grid
                ref={ref}
                {...props}
                container
                sx={{
                    alignItems: "center",
                    justifyContent: "center"
                }}
            />
        );
    }
);

export default GridContainer;
