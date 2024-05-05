import React, { useContext, useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  AppBar,
  Box,
  Toolbar,
  IconButton,
  Typography,
  Menu,
  Container,
  Button,
  Tooltip,
  MenuItem
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import SettingsIcon from '@mui/icons-material/Settings';

import AuthContext from "../context/AuthContext";
import { isChiefTech, isRegularTech } from "../utils/Permissions";


function ApplicationBar() {
  const [anchorElNav, setAnchorElNav] = useState(null);
  const [anchorElUser, setAnchorElUser] = useState(null);
  const { user, logoutUser } = useContext(AuthContext);
  const mainTitle = "InColor";
  const navigate = useNavigate();

  let [pages, setPages] = useState([]);

  useEffect(() => {
    setPages([]);
    if (isRegularTech(user)) {
      setPages([["Расписание", "/schedule"]]);
    }
    if (isChiefTech(user)) {
      setPages([["Расписание", "/schedule"], ["Операции", "/"]]);
    }
  }, [user]);

  const handleOpenNavMenu = (event) => {
    setAnchorElNav(event.currentTarget);
  };
  const handleOpenUserMenu = (event) => {
    setAnchorElUser(event.currentTarget);
  };

  const handleCloseNavMenu = () => {
    setAnchorElNav(null);
  };

  const handleCloseUserMenu = () => {
    setAnchorElUser(null);
  };

  const logoutUserAndCloseUserMenu = () => {
    logoutUser();
    handleCloseUserMenu();
  }

  const titleElement = (xsValue, mdValue, flexGrowValue = 0) => {
    return (
      <Typography
        variant="h5" noWrap component="a"
        href="/"
        sx={{
          mr: 2,
          display: { xs: xsValue, md: mdValue },
          flexGrow: flexGrowValue,
          fontFamily: 'monospace',
          fontWeight: 700,
          letterSpacing: '.3rem',
          color: 'inherit',
          textDecoration: 'none',
        }}
      >
        {mainTitle}
      </Typography>
    )
  }

  const settingsMenu = () => {
    if (user) return (
      <Box sx={{ flexGrow: 0 }}>
        <Tooltip title="Open settings">
          <Button onClick={handleOpenUserMenu} sx={{ p: 0 }}>
            <SettingsIcon style={{ color: '#FFFFFF' }} />
          </Button>
        </Tooltip>
        <Menu
          sx={{ mt: '45px' }}
          id="menu-appbar"
          anchorEl={anchorElUser}
          anchorOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
          keepMounted
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
          open={Boolean(anchorElUser)}
          onClose={handleCloseUserMenu}
        >
          <MenuItem>
            <Link style={{ textDecoration: "none", color: "black" }}
              onClick={handleCloseUserMenu} to="/profile" state={{ email: user.email }}>ПРОФИЛЬ</Link>
          </MenuItem>
          <MenuItem>
            <Link style={{ textDecoration: "none", color: "black" }}
              onClick={logoutUserAndCloseUserMenu} to="/login">ВЫЙТИ</Link>
          </MenuItem>
        </Menu>
      </Box>
    )
    else return (
      <Box sx={{ flexGrow: 0 }}>
        <Link to="/login" style={{ textDecoration: "none", color: "white" }}>ВОЙТИ</Link>
      </Box>
    )
  }

  return (
    <AppBar position="static">
      <Container maxWidth="xl">
        <Toolbar disableGutters>
          {titleElement('none', 'flex')}

          <Box sx={{ flexGrow: 1, display: { xs: 'flex', md: 'none' } }}>
            <IconButton
              size="large"
              aria-label="account of current user"
              aria-controls="menu-appbar"
              aria-haspopup="true"
              onClick={handleOpenNavMenu}
              color="inherit"
              hidden={pages?.length === 0}
            >
              <MenuIcon />
            </IconButton>
            <Menu
              id="menu-appbar"
              anchorEl={anchorElNav}
              anchorOrigin={{
                vertical: 'bottom',
                horizontal: 'left',
              }}
              keepMounted
              transformOrigin={{
                vertical: 'top',
                horizontal: 'left',
              }}
              open={Boolean(anchorElNav)}
              onClose={handleCloseNavMenu}
              sx={{
                display: { xs: 'block', md: 'none' },
              }}
            >
              {pages.map(([page, linkTo]) => (
                <MenuItem style={{ textDecoration: "none", color: "black" }} key={page} 
                  onClick={() => { navigate(linkTo); handleCloseNavMenu(); }}>
                  <Typography textAlign="center">{page}</Typography>
                </MenuItem>
              ))}
            </Menu>
          </Box>

          {titleElement('flex', 'none', 1)}

          <Box sx={{ flexGrow: 1, display: { xs: 'none', md: 'flex' } }}>
            {pages.map(([page, linkTo]) => (
              <Button
                key={page}
                onClick={handleCloseNavMenu}
                href={linkTo}
                sx={{ textDecoration: "none", my: 2, color: 'white', display: 'block' }}
              >
                {page}
              </Button>
            ))}
          </Box>

          {settingsMenu()}

        </Toolbar>
      </Container>
    </AppBar>
  );
}
export default ApplicationBar;
