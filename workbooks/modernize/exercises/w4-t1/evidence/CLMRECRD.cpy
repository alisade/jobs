      *================================================================*
      * CLMRECRD  CLAIMDESK PAID-LOSS RECONCILIATION RECORD  (2011)     *
      * RECFM=FB LRECL=45 (TRANSFERRED AS ASCII TEXT, LF TERMINATED)    *
      *================================================================*
       01  CLMRECON-RECORD.
           05  CR-CLAIM-NUMBER        PIC X(15).
           05  CR-PAID-DATE           PIC X(09).
      *        DD-MON-YY, MON IN JAN FEB MAR APR MAY JUN JUL AUG SEP
      *        OCT NOV DEC (MIXED CASE ACCEPTED)
           05  CR-AMOUNT              PIC X(13).
           05  CR-STATUS              PIC X(08).
