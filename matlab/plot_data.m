clear all
close  % Close any open figures

% Get the file from the user
[FILENAME, PATHNAME] = uigetfile('*.tsv');

% Get the data from the file
my_data = benchDecoder([PATHNAME '\' FILENAME]);

% Parse the data
delta = my_data(:,2);
voltage = my_data(:,4);
current = my_data(:,5);
power = my_data(:,6);

tData = 7;
if size(my_data,2) == 17
    tData = tData + 5;
end

temperature1 = my_data(:,tData); tData = tData + 1;
temperature2 = my_data(:,tData); tData = tData + 1;
temperature3 = my_data(:,tData); tData = tData + 1;
temperature4 = my_data(:,tData);

demand = my_data(:,8);

% Plot the data
subplot(2,2,1)
[haxes,hline1,hline2] = plotyy(delta, voltage, delta, current);
xlabel('Time /s');
ylabel(haxes(1),'Voltage /V');
ylabel(haxes(2),'Current /A');

subplot(2,2,2);plot(delta, power);
xlabel('Time /s');
ylabel('Power /W');

subplot(2,2,3);plot(delta, demand);
xlabel('Time /s');
ylabel('Demand /A');

subplot(2,2,4)
plot(delta, temperature1); hold all;
plot(delta, temperature2);
plot(delta, temperature3);
plot(delta, temperature4);
xlabel('Time /s');
ylabel('Temperature /degC');

clear all