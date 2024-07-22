import React from 'react';
import { HashLink } from 'react-router-hash-link';
import { AppBar, Tabs, Tab, Typography, useTheme, Box } from '@mui/material';

const TopBar = () => {
    const theme = useTheme();

    return (
        <AppBar
            position="fixed"
            sx={{
                backgroundColor: '#FFFFFF',
                height: '5rem',
                boxShadow: 'none',
                borderBottom: '1px solid #E0E0E0',
                zIndex: theme.zIndex.drawer + 1, // Ensure AppBar is above other content
            }}
        >
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                width: '100%',
                height: '100%'
            }}>
                <Typography
                    variant="h6"
                    component={HashLink}
                    smooth to="/#"
                    sx={{
                        fontSize: '1.5rem',
                        color: theme.palette.text.primary,
                        textDecoration: 'none',
                        marginLeft: '1rem',
                        '&:hover': {
                            color: theme.palette.primary.main,
                        },
                    }}
                >
                    Hanliang Xu
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Tabs
                        sx={{
                            '& .MuiTab-root': {
                                fontSize: '1rem',
                                fontFamily: theme.typography.fontFamily,
                                minWidth: 'auto',
                                padding: '0 1rem',
                                color: theme.palette.text.primary,
                                '&:hover': {
                                    color: theme.palette.primary.main,
                                },
                                '&.Mui-selected': {
                                    color: theme.palette.primary.main,
                                    fontWeight: 'bold',
                                }
                            }
                        }}
                    >
                        <Tab label="About" component={HashLink} smooth to="#about" />
                    </Tabs>
                    <Box
                        component="span"
                        sx={{
                            fontSize: '1rem',
                            color: theme.palette.text.primary,
                            margin: '0 0.5rem',
                            display: 'flex',
                            alignItems: 'center'
                        }}
                    >
                        /
                    </Box>
                    <Tabs
                        sx={{
                            '& .MuiTab-root': {
                                fontSize: '1rem',
                                fontFamily: theme.typography.fontFamily,
                                minWidth: 'auto',
                                padding: '0 1rem',
                                color: theme.palette.text.primary,
                                '&:hover': {
                                    color: theme.palette.primary.main,
                                },
                                '&.Mui-selected': {
                                    color: theme.palette.primary.main,
                                    fontWeight: 'bold',
                                }
                            }
                        }}
                    >
                        <Tab label="JSON Upload" component={HashLink} smooth to="/json-upload" />
                    </Tabs>
                </Box>
            </div>
        </AppBar>
    );
};

export default TopBar;
