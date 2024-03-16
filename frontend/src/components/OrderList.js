import React, { useState, useEffect, useContext } from "react";
import InfoIcon from "@mui/icons-material/Info";
import {
  Typography,
  Grid, Stack,
  Button,
  Paper
} from "@mui/material";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { DataGrid, GridToolbar, ruRU } from "@mui/x-data-grid";
import { ruRU as coreruRU } from "@mui/material/locale";
import { useNavigate } from "react-router-dom";

import AuthContext from "../context/AuthContext";
import orderService from "../servicies/OrderService";


const OrderList = () => {
  const { authTokens } = useContext(AuthContext);
  const [orders, setOrders] = useState([]);

  const navigate = useNavigate();
  const columns = [
    { field: "user", headerName: "ФИО стоматолога", width: 150 },
    { field: "date", headerName: "Дата оформления", width: 150 },
    { field: "status", headerName: "Статус", width: 300 },
    { field: "discount", headerName: "Скидка", width: 80 },
    { field: "cost", headerName: "Сумма", width: 100 },
    {
      field: "info", headerName: "Подробнее", sortable: false,
      disableExport: true,
      renderCell: (params) => {
        return (
          <Button variant="contained"
            onClick={() => navigate("/order", { state: { order: params.row.orderInfo } })}>
            <InfoIcon />
          </Button>
        )
      }
    }
  ];

  useEffect(() => {
    if (!authTokens || !authTokens.access) {
      navigate("/login");
      return;
    }

    getOrders();
  }, []);

  const theme = createTheme(
    {
      palette: {
        primary: { main: "#1976d2" },
      },
    },
    ruRU, // x-data-grid translations
    coreruRU // core translations
  );

  const getOrders = () => {
    orderService.getOrders()
      .then(res => {
        const result = res.data.map(function (order) {
          return {
            id: order.id,
            user: order.user.last_name + " " + order.user.first_name,
            status: order.status.name,
            discount: order.discount * 100 + "%",
            cost: order.cost.toFixed(2),
            date: order.order_date,
            orderInfo: order
          }
        });
        setOrders(result);
      })
      .catch(err => {
        console.log(err);
      });
  }

  return (
    <Grid container sx={{
      spacing: 0,
      direction: "column",
      alignItems: "center",
      justifyContent: "center"
    }}>
      <Stack container sx={{
        display: "flex",
        minWidth: "500px",
        spacing: 3
      }}>
        <Typography variant="h4" component="h5" sx={{
          textAlign: "center",
          paddingY: 2
        }}>
          Заказы
        </Typography>
        {
          orders.length > 0 ?
            <Stack>
              <ThemeProvider theme={theme}>
                <DataGrid
                  sx={{
                    padding: 2,
                    width: "100%",
                  }}
                  rows={orders}
                  columns={columns}
                  initialState={{
                    pagination: {
                      paginationModel: { page: 0, pageSize: 10 },
                    },
                  }}
                  pageSizeOptions={[10, 20, 30, 40, 50, 100]}
                  slots={{ toolbar: GridToolbar }}
                  ruRU
                  disableRowSelectionOnClick
                  slotProps={{
                    toolbar: {
                      csvOptions: {
                        fileName: 'Заказы',
                        delimiter: ';',
                        utf8WithBom: true
                      }
                    }
                  }}
                >
                  <GridToolbar />
                </DataGrid>
              </ThemeProvider>
            </Stack>
            : <Typography component={Paper} sx={{
              margin: 2,
              padding: 2,
              textAlign: 'center'
            }}>
              Нет заказов
            </Typography>
        }
      </Stack>
    </Grid>
  )
}

export default OrderList;