import React from 'react';
import {Box, Typography} from '@mui/material';

function Section({title, content}) {
    return (
        <Box my={4}>
            <Typography variant="h4" gutterBottom>{title}</Typography>
            <Typography variant="body1">
                {content}
            </Typography>
            {/* If you have images specific to sections, you can place them here */}
            {/* For instance, for the 'PROJECTS' section, you might want to showcase screenshots of your projects */}
            {/* <img src="path_to_your_image.jpg" alt="Description of image" /> */}
        </Box>
    );
}

export default Section;