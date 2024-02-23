import React, { useState, useEffect, useContext } from 'react';
import InfoIcon from '@mui/icons-material/Info';
import VisibilityIcon from '@mui/icons-material/Visibility';
import {
  Typography,
  Grid, Stack, Box,
  TextField,
  Table, TableContainer, TableHead, TableBody, TableRow, TableCell,
  Button,
  Paper,
  Popper, Fade
} from '@mui/material';
import PopupState, { bindToggle, bindPopper } from 'material-ui-popup-state';

import AuthContext from '../context/AuthContext';
import orderService from '../servicies/OrderService';
import { useNavigate } from 'react-router-dom';
import productService from '../servicies/ProductService';
import ToothMarks from './ToothMarks';


const PhysicianOrderList = () => {
  const { authTokens, userGroupToString } = useContext(AuthContext);
  const [userGroup, setUserGroup] = useState(userGroupToString());
  const [orders, setOrders] = useState([]);
  const [products, setProducts] = useState([]);
  const [currOrder, setCurrOrder] = useState({});
  const navigate = useNavigate();

  useEffect(() => {
    if (!authTokens || !authTokens.access) {
      navigate('/login');
      return;
    }
    if (userGroup === "Врач") {
      orderService.getOrdersForUser(authTokens.access)
        .then(res => {
          setOrders(res.data);
          if (res.data.length > 0) {
            setCurrOrder(res.data[0]);
            getOrderInfo(res.data[0]);
          }
        })
        .catch(err => {
          console.log(err);
        });
    }
  }, []);

  const getOrderInfo = (order) => {
    productService.getForOrder(authTokens.access, order.id)
      .then(res => {
        setProducts(res.data);
        setCurrOrder(order);
      })
      .catch(err => {
        setProducts([]);
        setCurrOrder({});
        console.log(err);
      });
  }

  // Main variable to render orders on the screen
  const renderOrders = () => {
    let i = 1;
    return orders.map((order) => (
      <TableRow key={order.id}>
        <TableCell>{i++}</TableCell>
        <TableCell sx={{ textWrap: "nowrap" }}>{order.order_date}</TableCell>
        <TableCell>{order.status.name}</TableCell>
        <TableCell sx={{ textAlign: "center" }}>
          <Button onClick={() => getOrderInfo(order)}>
            <InfoIcon />
          </Button>
        </TableCell>
      </TableRow>
    ));
  };

  const renderProducts = () => {
    let i = 1;
    console.log(products);
    return products.map(product => (
      <TableRow key={product.id}>
        <TableCell>{i++}</TableCell>
        <TableCell>{product.product_type.name}</TableCell>
        <TableCell>{product.product_status.name}</TableCell>
        <TableCell>{product.amount}</TableCell>
        <TableCell>{product.product_type.cost.toFixed(2)}</TableCell>
        <TableCell>{product.discount * 100}%</TableCell>
        <TableCell>{product.cost.toFixed(2)}</TableCell>
        <TableCell>
          <PopupState variant="popper" popupId="demo-popup-popper">
            {(popupState) => (
              <div>
                <Button variant="contained" {...bindToggle(popupState)}>
                  <VisibilityIcon />
                </Button>
                <Popper {...bindPopper(popupState)} transition
                  placement={'bottom-end'}
                >
                  {({ TransitionProps }) => (
                    <Fade {...TransitionProps} timeout={350}>
                      <Paper>
                        <Typography sx={{ p: 1 }}>
                          <ToothMarks teethList={product.teeth} />
                        </Typography>
                      </Paper>
                    </Fade>
                  )}
                </Popper>
              </div>
            )}
          </PopupState>
        </TableCell>
      </TableRow>
    ));
  }

  return (
    <Grid container spacing={3} wrap="wrap-reverse">
      <Grid item xs={4}>
        <h3 className='m-4 mt-5'>Заказы</h3>
        <Button variant="contained" onClick={() => { navigate("/create_order") }}
          sx={{
            margin: "15px"
          }}>
          Оформить заказ
        </Button>
        {
          orders.length > 0 ?
            <TableContainer component={Paper} sx={{ margin: 2, padding: 2 }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>№</TableCell>
                    <TableCell>Дата</TableCell>
                    <TableCell>Статус</TableCell>
                    <TableCell></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {renderOrders()}
                </TableBody>
              </Table>
            </TableContainer>
            : <Typography component={Paper} sx={{
              margin: 2,
              padding: 2,
              textAlign: 'center'
            }}>
              Нет заказов
            </Typography>
        }
      </Grid>
      <Grid item xs={8}>
        <Box sx={{
          border: 1,
          borderRadius: 2,
          borderColor: '#4d4c4c',
          padding: 3,
          marginTop: 5,
        }}>
          <Typography textAlign={"center"} variant="h4" component="h4" sx={{ marginBottom: 2 }}>
            Информация о заказе
          </Typography>
          <Box>
            <Stack spacing={2}>
              {
                products.length > 0 ?
                  <TableContainer component={Paper}>
                    <Table label='Изделия'>
                      <TableHead>
                        <TableRow>
                          <TableCell>№</TableCell>
                          <TableCell>Тип изделия</TableCell>
                          <TableCell>Статус</TableCell>
                          <TableCell sx={{ width: "10%" }}>Кол-во</TableCell>
                          <TableCell>Цена</TableCell>
                          <TableCell>Скидка</TableCell>
                          <TableCell>Сумма</TableCell>
                          <TableCell>Отметки</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {renderProducts()}
                      </TableBody>
                    </Table>
                  </TableContainer>
                  : <p for="products">Изделия для заказа</p>
              }
              <TextField
                InputProps={{ readOnly: true }}
                InputLabelProps={{ shrink: true }}
                label="Статус"
                variant="outlined"
                value={currOrder?.status?.name}
              />
              <Grid sx={{
                display: "flex",
                direction: "row",
              }}>
                {
                  currOrder?.discount !== 0 ?
                    <>
                      <TextField item
                        sx={{ width: "100%"}}
                        InputProps={{ readOnly: true }}
                        InputLabelProps={{ shrink: true }}
                        label="Сумма заказа (руб)"
                        variant="outlined"
                        value={currOrder?.cost?.toFixed(2)}
                      />
                      <TextField item
                        sx={{ width: "100%", marginX: 2 }}
                        InputProps={{ readOnly: true }}
                        InputLabelProps={{ shrink: true }}
                        label="Скидка"
                        variant="outlined"
                        value={currOrder?.discount * 100 + "%"}
                      />
                    </>
                    : <></>
                }
                <TextField item
                  sx={{ width: "100%"}}
                  InputProps={{ readOnly: true }}
                  InputLabelProps={{ shrink: true }}
                  label="Итоговая сумма заказа (руб)"
                  variant="outlined"
                  value={(currOrder?.cost * (1 - currOrder?.discount)).toFixed(2)}
                />
              </Grid>
              <TextField
                InputProps={{ readOnly: true }}
                InputLabelProps={{ shrink: true }}
                label="Дата"
                variant="outlined"
                value={currOrder?.order_date}
              />
            </Stack>
          </Box>
        </Box>
      </Grid>
    </Grid>
  )
}

export default PhysicianOrderList;