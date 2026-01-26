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
  MenuItem,
} from '@mui/material';
import { ArrowForward, ArrowBack, Add, Delete } from '@mui/icons-material';

interface Vendor {
  id: string;
  name: string;
  category: string;
  email: string;
  phone: string;
}

interface Props {
  data: Vendor[];
  onUpdate: (data: Vendor[]) => void;
  onNext: () => void;
  onBack: () => void;
}

const categoryOptions = [
  { value: 'rental', label: 'Rental' },
  { value: 'subcontractor', label: 'Subcontractor' },
  { value: 'outside_service', label: 'Outside Service' },
  { value: 'material_supplier', label: 'Material Supplier' },
];

export default function VendorsStep({ data, onUpdate, onNext, onBack }: Props) {
  const [vendors, setVendors] = useState<Vendor[]>(
    data.length > 0
      ? data
      : [{ id: '1', name: '', category: 'subcontractor', email: '', phone: '' }]
  );

  const handleAdd = () => {
    setVendors([
      ...vendors,
      { id: Date.now().toString(), name: '', category: 'subcontractor', email: '', phone: '' },
    ]);
  };

  const handleRemove = (id: string) => {
    if (vendors.length > 1) {
      setVendors(vendors.filter((v) => v.id !== id));
    }
  };

  const handleChange = (id: string, field: keyof Vendor, value: string) => {
    setVendors(vendors.map((v) => (v.id === id ? { ...v, [field]: value } : v)));
  };

  const handleNext = () => {
    const validVendors = vendors.filter((v) => v.name.trim() !== '');
    onUpdate(validVendors);
    onNext();
  };

  const handleSkip = () => {
    onUpdate([]);
    onNext();
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Vendor Contacts
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Add your vendor contacts (optional - you can also add these later)
      </Typography>

      <TableContainer component={Paper} sx={{ mt: 2 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Phone</TableCell>
              <TableCell width={100}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {vendors.map((vendor) => (
              <TableRow key={vendor.id}>
                <TableCell>
                  <TextField
                    fullWidth
                    placeholder="Vendor name"
                    value={vendor.name}
                    onChange={(e) => handleChange(vendor.id, 'name', e.target.value)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    fullWidth
                    select
                    value={vendor.category}
                    onChange={(e) => handleChange(vendor.id, 'category', e.target.value)}
                    size="small"
                  >
                    {categoryOptions.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </TextField>
                </TableCell>
                <TableCell>
                  <TextField
                    fullWidth
                    type="email"
                    placeholder="email@example.com"
                    value={vendor.email}
                    onChange={(e) => handleChange(vendor.id, 'email', e.target.value)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    fullWidth
                    placeholder="555-1234"
                    value={vendor.phone}
                    onChange={(e) => handleChange(vendor.id, 'phone', e.target.value)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <IconButton
                    onClick={() => handleRemove(vendor.id)}
                    disabled={vendors.length === 1}
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

      <Button startIcon={<Add />} onClick={handleAdd} sx={{ mt: 2 }}>
        Add Vendor
      </Button>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
        <Button onClick={onBack} startIcon={<ArrowBack />}>
          Back
        </Button>
        <Box>
          <Button onClick={handleSkip} sx={{ mr: 1 }}>
            Skip
          </Button>
          <Button variant="contained" onClick={handleNext} endIcon={<ArrowForward />}>
            Next
          </Button>
        </Box>
      </Box>
    </Box>
  );
}
