import torch
import torch.nn as nn

from ml_lib.model import Model

class LSTM_Net(Model):
    """
    Pytorch LSTM Network

    Attributes:
        n_layers: Number of layers in the LSTM. Used to initialize hidden state
        hidden_dim. Size of hidden dimension of LSTM. Used to initialize hidden
        state
        dropout: Dropout operation
        actv: Activation function. Defaults to ReLU
        out_actv: Activation function for the output. Assumes None unless passed
        lstm: LSTM layer or layers of the network
        fc: List of intermediate linear layers
        out: Output layer
    """
    def __init__(self,
                 fc,
                 input_dim,
                 output_dim,
                 hidden_dim,
                 n_layers,
                 non_seq_dim=None,
                 dropout=0.5,
                 out_actv=None):
        """
        Constructor.

        Parameters:
            fc: Iterable containing the number of neurons for each layer
            input_dim: Input dimensions
            output_dim: Output dimensions
            hidden_dim: LSTM hidden dimensions
            n_layers: Number of LSTM layers
            non_seq_dim: Non sequential data dimensions. Use if you want to
            append extra data onto the output of the LSTM module
            dropout: Probability to use for dropout layers. Defaults to 0.5
            out_actv: Pytroch activation function to use on final output. Is not
            called if None
        """
        super(LSTM_Net, self).__init__()
        
        self.n_layers = n_layers
        self.hidden_dim = hidden_dim

        self.dropout = nn.Dropout(dropout)
        if n_layers == 1: dropout = 0
        self.actv = nn.ReLU()
        self.out_actv = out_actv

        self.lstm = nn.LSTM(input_dim, hidden_dim, n_layers,
                            dropout=dropout, batch_first=True)

        prev_out = hidden_dim + (non_seq_dim if non_seq_dim else 0)
        self.fc = []
        for i,neurons in enumerate(fc):
            self.fc.append(nn.Linear(prev_out, neurons))
            prev_out = neurons
        self.out = nn.Linear(prev_out, output_dim)

        # Convert parameters to float
        self.float()

    def forward(self, x, non_seq=None):
        """
        Forward pass of the network

        Parameters:
            x: Input of size (batch, seq_length, input_dim)
            non_seq: Optional input of non sequential data to be appended after
            the LSTM module, of size (batch, non_seq_dim)

        Returns:
            Tensor: Output of size (batch, output_dim)
        """
        x = x.float()
        batch_size = x.size(0)
        lstm_out, self.hidden = self.lstm(x, self.init_hidden(batch_size))
        # Save only the final hidden state for each sequence
        lstm_out = lstm_out[:, -1, :]

        # Append non_sequential data after LSTM processing
        if non_seq is None:
            dense = lstm_out
        else:
            non_seq = non_seq.float()
            dense = torch.cat((lstm_out, non_seq), dim=1)
        for l in self.fc:
            dense = l(dense)
            dense = self.actv(dense)
            dense = self.dropout(dense)
        out = self.out(dense)
        if self.out_actv: out = self.out_atcv(out)
        return out

    def init_hidden(self, batch_size):
        """
        Initializes an empty hidden state

        Parameters:
            batch_size: Batch size this hidden state will be used for

        Returns:
            Tuple: Hidden state composed of two tensors of size (n_layers,
            batch_size, hidden_dim)
        """
        weight = next(self.parameters()).data

        hidden = (weight.new(self.n_layers, batch_size,
                             self.hidden_dim).zero_(),
                      weight.new(self.n_layers, batch_size,
                                 self.hidden_dim).zero_())
        return hidden

if __name__ == "__main__":
    # Tests
    input_dim = 100
    batch_size = 32
    seq_len = 16
    non_seq_dim = 5
    model = LSTM_Net(fc=[128],
                     input_dim=input_dim,
                     output_dim=1,
                     hidden_dim=128,
                     n_layers=1,
                     non_seq_dim=non_seq_dim,
                     dropout=0.5)
    import numpy as np
    inputs = np.random.random((batch_size, seq_len, input_dim))
    non_seq = np.random.random((batch_size, non_seq_dim))
    inputs = torch.from_numpy(inputs)
    non_seq = torch.from_numpy(non_seq)
    out = model(inputs, non_seq=non_seq)