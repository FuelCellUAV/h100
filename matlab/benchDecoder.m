function [ output ] = benchDecoder( file )
%benchDecoder Function to decode data from the ground test station for the
%FuelCellUAV project at Loughborough University.
%   Takes in the FuelCellUAV bench test logfile and outputs a MATLAB array
%
% Copyright (C) 2014  Simon Howroyd
% 
%     This program is free software: you can redistribute it and/or modify
%     it under the terms of the GNU General Public License as published by
%     the Free Software Foundation, either version 3 of the License, or
%     (at your option) any later version.
% 
%     This program is distributed in the hope that it will be useful,
%     but WITHOUT ANY WARRANTY; without even the implied warranty of
%     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
%     GNU General Public License for more details.
% 
%     You should have received a copy of the GNU General Public License
%     along with this program.  If not, see <http://www.gnu.org/licenses/>.

%% Preamble
    % Declare some variables
    data = [];
    output = [];  
    
%% Extract the data from the file into MATLAB
    % Open the input file
    log = fopen(file,'rt');
    
    % Get the first line
    this_line = fgetl(log);
    
    % Decode the rest of the file the same as line 1
    while this_line >= 0
        A = textscan(this_line, '%s', 'delimiter', '\t');
        try
            data = [data ; A{1}'];
        catch  % Do nothing, eliminates any dodgy records
        end
        this_line = fgetl(log);  % Get the next line
    end
    
    % Close the input file, no longer needed
    fclose(log);
    
%% Convert the data to a useable format
    % Find out how much data we have
    [rows,cols] = size(data);
    
    % Convert the data to a matrix of numbers. Leave blank any text cells
    for c=1:cols
        for r=1:rows
            try
                output(r,c) = str2num(cell2mat(data(r,c)));
            catch
                % Do nothing
            end
        end
    end   
end

