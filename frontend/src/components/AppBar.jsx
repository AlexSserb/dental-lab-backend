import React, { useContext, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  AppBar,
  Box,
  Toolbar,
  IconButton,
  Typography,
  Menu,
  Container,
  Button,
  MenuItem
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";

import AuthContext from "../context/AuthContext";
import { isChiefTech, isRegularTech } from "../utils/Permissions";
import { dropdownMenuButtonStyle, menuButtonStyle } from "./styles/AppBarStyles";

function ApplicationBar() {
  const [anchorElNav, setAnchorElNav] = useState(null);
  const { user } = useContext(AuthContext);
  const mainTitle = "InColor";
  const navigate = useNavigate();

  const [pages, setPages] = useState([]);

  const pagesData = {
    profile: ["Профиль", "/profile", { email: user?.email }],
    schedule: ["Расписание", "/schedule", {}],
    operationsForChief: ["Операции", "/", {}],
  };

  useEffect(() => {
    if (!user) return;

    if (isRegularTech(user)) {
      setPages([pagesData.profile, pagesData.schedule]);
    }
    else if (isChiefTech(user)) {
      setPages([pagesData.profile, pagesData.schedule, pagesData.operationsForChief]);
    }
    else {
      setPages([pagesData.profile]);
    }
  }, [user]);

  const handleOpenNavMenu = (event) => {
    setAnchorElNav(event.currentTarget);
  };

  const handleCloseNavMenu = () => {
    setAnchorElNav(null);
  };

  const handleMenuButtonClick = (page, state) => {
    navigate(page, { state: state });
    handleCloseNavMenu();
  };

  const titleElement = (xsValue, mdValue, flexGrowValue = 0) => {
    return (
      <Typography
        variant="h4"
        noWrap
        component="a"
        href="/"
        sx={{
          margin: 1,
          marginRight: 5,
          display: { xs: xsValue, md: mdValue },
          flexGrow: flexGrowValue,
          fontWeight: 600,
          letterSpacing: ".2rem",
          color: "inherit",
          textDecoration: "none",
        }}
      >
        {mainTitle}
      </Typography>
    );
  };

  return (
    <AppBar position="static">
      <Container maxWidth="xl">
        <Toolbar disableGutters>
          {titleElement("none", "flex")}

          <Box sx={{ flexGrow: 1, display: { xs: "flex", md: "none" } }}>
            <IconButton
              size="large"
              aria-label="account of current user"
              aria-controls="menu-appbar"
              aria-haspopup="true"
              onClick={handleOpenNavMenu}
              color="inherit"
            >
              <MenuIcon />
            </IconButton>
            <Menu
              id="menu-appbar"
              anchorEl={anchorElNav}
              anchorOrigin={{
                vertical: "bottom",
                horizontal: "left",
              }}
              keepMounted
              transformOrigin={{
                vertical: "top",
                horizontal: "left",
              }}
              open={Boolean(anchorElNav)}
              onClose={handleCloseNavMenu}
              sx={{
                display: { xs: "block", md: "none" },
              }}
            >
              {
                pages.map(([page, linkTo, state]) => (
                  <MenuItem style={dropdownMenuButtonStyle} key={page}
                    onClick={() => handleMenuButtonClick(linkTo, state)}>
                    <Typography textAlign="center">{page}</Typography>
                  </MenuItem>
                ))
              }
            </Menu>
          </Box>

          {titleElement("flex", "none", 1)}

          <Box sx={{ flexGrow: 1, display: { xs: "none", md: "flex" } }}>
            {
              pages.map(([page, linkTo, state]) => (
                <Button
                  key={page}
                  onClick={() => handleMenuButtonClick(linkTo, state)}
                  sx={menuButtonStyle}
                >
                  <Typography variant="h6">
                    {page}
                  </Typography>
                </Button>
              ))
            }
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}
export default ApplicationBar;
