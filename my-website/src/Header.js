import React from 'react';
import { Typography, Link, Box } from '@mui/material';

function Header() {
  return (
    <Box my={4}>
      <Typography variant="h2" gutterBottom>Hanliang Xu</Typography>
      <Typography variant="body1">
        615-853-4552 | <Link href="mailto:hanliang.xu@vanderbilt.edu">hanliang.xu@vanderbilt.edu</Link> | <Link href="https://www.linkedin.com/in/leon-xu-b79062239/">LinkedIn</Link> | <Link href="https://github.com/Hanliang-Xu">GitHub</Link>
      </Typography>
      {/* Consider adding a profile picture here */}
      {/* <img src="path_to_your_image.jpg" alt="Hanliang Xu" /> */}
    </Box>
  );
}

export default Header;