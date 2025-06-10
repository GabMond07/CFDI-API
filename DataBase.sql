-- tabla usuario
CREATE TABLE User (
    User_ID INT PRIMARY KEY,
    Username VARCHAR(100),
    Email VARCHAR(150),
    Password VARCHAR(100),
    Role VARCHAR(50),
    Api_Token VARCHAR(255),
    Tenant_ID VARCHAR(100)
);

-- tabla emisor
CREATE TABLE Issuer (
    Issuer_ID INT PRIMARY KEY,
    RFC_Issuer VARCHAR(20),
    Name_Issuer VARCHAR(150),
    Tax_Regime VARCHAR(100)
);

-- tabla receptor
CREATE TABLE Receiver (
    Receiver_ID INT PRIMARY KEY,
    RFC_Receiver VARCHAR(20),
    Name_Receiver VARCHAR(150),
    CFDI_Use VARCHAR(50),
    Tax_Regime VARCHAR(100),
    Tax_Address VARCHAR(255)
);

-- tabla CFDI
CREATE TABLE CFDI (
    CFDI_ID INT PRIMARY KEY,
    UUID INT,
    Issue_Date DATE,
    Payment_Method VARCHAR(50),
    Currency VARCHAR(10),
    Voucher_Type VARCHAR(50),
    Total DOUBLE,
    Subtotal DOUBLE,
    User_ID INT,
    Payment_Form VARCHAR(50),
    Issuer_ID INT,
    Receiver_ID INT,
    FOREIGN KEY (User_ID) REFERENCES User(User_ID),
    FOREIGN KEY (Issuer_ID) REFERENCES Issuer(Issuer_ID),
    FOREIGN KEY (Receiver_ID) REFERENCES Receiver(Receiver_ID)
);

-- tabla concepto
CREATE TABLE Concept (
    Concept_ID INT PRIMARY KEY,
    CFDI_ID INT,
    Fiscal:Key VARCHAR(50),
    Description TEXT,
    Quantity DOUBLE,
    Unit_Value DOUBLE,
    Amount DOUBLE,
    Discount DOUBLE,
    FOREIGN KEY (CFDI_ID) REFERENCES CFDI(CFDI_ID)
);

-- tabla impuestos
CREATE TABLE Taxes (
    Tax_ID INT PRIMARY KEY,
    Concept_ID INT,
    Type VARCHAR(50),
    Tax VARCHAR(50),
    Rate DOUBLE,
    Amount DOUBLE,
    FOREIGN KEY (Concept_ID) REFERENCES Concept(Concept_ID)
);

-- tabla complementoPago
CREATE TABLE PaymentComplement (
    Payment_ID INT PRIMARY KEY,
    CFDI_ID INT,
    Payment_Date DATE,
    Payment_Form VARCHAR(50),
    Payment_Currency VARCHAR(10),
    Payment_Amount DOUBLE,
    FOREIGN KEY (CFDI_ID) REFERENCES CFDI(CFDI_ID)
);
