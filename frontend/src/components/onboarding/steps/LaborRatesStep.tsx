import { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import { ArrowForward, ArrowBack, Add, Delete } from '@mui/icons-material';

interface LaborRate {
  id: string;
  type: string;
  hourly_rate: number;
}

interface Props {
  data: LaborRate[];
  onUpdate: (data: LaborRate[]) => void;
  onNext: () => void;
  onBack: () => void;
}

export default function LaborRatesStep({ data, onUpdate, onNext, onBack }: Props) {
  const [rates, setRates] = useState<LaborRate[]>(
    data.length > 0 ? data : [{ id: '1', type: '', hourly_rate: 0 }]
  );

  const handleAdd = () => {
    setRates([...rates, { id: Date.now().toString(), type: '', hourly_rate: 0 }]);
  };

  const handleRemove = (id: string) => {
    if (rates.length > 1) {
      setRates(rates.filter((r) => r.id !== id));
    }
  };

  const handleChange = (id: string, field: keyof LaborRate, value: string | number) => {
    setRates(
      rates.map((r) =>
        r.id === id ? { ...r, [field]: field === 'hourly_rate' ? parseFloat(value as string) || 0 : value } : r
      )
    );
  };

  const handleNext = () => {
    // Filter out empty rows
    const validRates = rates.filter((r) => r.type.trim() !== '' && r.hourly_rate > 0);
    onUpdate(validRates);
    onNext();
  };

  const handleSkip = () => {
    onUpdate([]);
    onNext();
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Labor Rates
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Add your labor types and hourly rates (optional)
      </Typography>

      <TableContainer component={Paper} sx={{ mt: 2 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Labor Type</TableCell>
              <TableCell>Hourly Rate ($)</TableCell>
              <TableCell width={100}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rates.map((rate) => (
              <TableRow key={rate.id}>
                <TableCell>
                  <TextField
                    fullWidth
                    placeholder="e.g., Foreman, Laborer, Operator"
                    value={rate.type}
                    onChange={(e) => handleChange(rate.id, 'type', e.target.value)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    fullWidth
                    type="number"
                    placeholder="0.00"
                    value={rate.hourly_rate || ''}
                    onChange={(e) => handleChange(rate.id, 'hourly_rate', e.target.value)}
                    size="small"
                    inputProps={{ min: 0, step: 0.01 }}
                  />
                </TableCell>
                <TableCell>
                  <IconButton
                    onClick={() => handleRemove(rate.id)}
                    disabled={rates.length === 1}
                    size="small"
                    color="error"
                  >
                    <Delete />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Button
        startIcon={<Add />}
        onClick={handleAdd}
        sx={{ mt: 2 }}
      >
        Add Labor Type
      </Button>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
        <Button onClick={onBack} startIcon={<ArrowBack />}>
          Back
        </Button>
        <Box>
          <Button onClick={handleSkip} sx={{ mr: 1 }}>
            Skip
          </Button>
          <Button
            variant="contained"
            onClick={handleNext}
            endIcon={<ArrowForward />}
          >
            Next
          </Button>
        </Box>
      </Box>
    </Box>
  );
}
