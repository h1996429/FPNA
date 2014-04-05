#Parallel implementation
from multiprocessing import Queue, Lock, Event

#------------------------------------------------------------------------------
class Link():
  '''
  The Link resource.  It is connected to and from nodes and other Links.
  '''
  #----------------------------------------------------------------------------
  def __init__(self, W, T):
    '''
    '''
    assert isinstance(W, float), 'W must be an float'
    assert isinstance(T, float), 'T must be a float'

    self.ACKL = Lock()
    self.ACKCount = 0
    self.ACKEvent = Event()
    self.ACKCountMax = 0 #should be equal to len(outputList)

    self.dataQueue = Queue()
    self.queueEvent = Event()

    self.outputList = []
    self.inputList = []

    self.W = W
    self.T = T

    self.active = False
    return

  #----------------------------------------------------------------------------
  def activate(self):
    '''
    This is the function that will run as a seperate process.  Everything
    else in the class just access data.  Call this function when
    everything is connected and finalized.
    '''
    self.ackCountMax = len(self.outputList)
    self.queueEvent.clear()
    self.ACKEvent.clear()
    self.active = True
    while True:
      self.queueEvent.wait() #Wait until the queue has data
      x, R = self.dataQueue.get() #Get data from the queue
      R.ACK(self) #send an ACK to the resource that sent the data
      xp = self.W*x + self.T #Apply the affine transform
      assert self.ACKCount == 0, 'ACKCount is not 0 prior to outputting!'
      for r in self.outputList: #Send this value to each connected resource
        r.push(xp, self) 
      self.ACKEvent.wait() #Wait for all ACKs
      self.ACKCount = 0 #Reset the ACK count
      self.ACKEvent.clear()
      if self.dataQueue.empty():
        #This will probably only happen when the NN is totally idle
        self.queueEvent.clear()
    return

  #----------------------------------------------------------------------------
  def appendOutput(self, R):
    '''
    Simply appends the resource R to the outputList.  This is mostly for 
    checking for programmer errors, it isn't necessary.  I may remove this
    method in the future.
    '''
    if not isinstance(R, (Link, Activator)):
      raise TypeError('R must be a Link or an Activator')
    self.outputList.append(R)
    return

  #----------------------------------------------------------------------------
  def appendInput(self, R):
    '''
    Simply appends the resource R to the inputList.  This is mostly for 
    checking for programmer errors, it isn't necessary.  I may remove this
    method in the future.
    '''
    if not isinstance(R, (Link, Activator)):
      raise TypeError('R must be a Link or an Activator')
    self.inputList.append(R)
    return

  #----------------------------------------------------------------------------
  def push(self, x, R):
    '''
    The resource R pushes the value x to the Queue.  If R is not in the
    inputList, it is an error.
    '''
    if R not in self.inputList:
      raise RuntimeError('Received task from unconnected resource')
    else:
      self.dataQueue.put((x, R)) #Package into a tuple and put to Queu
      self.queueEvent.set() #Set the queue event
    return

  #----------------------------------------------------------------------------
  def ACK(self, R):
    '''
    The resource R sends an acknowledgement to this Link.  If R is not in the
    outputList, it is an error.
    '''
    if R not in self.outputList:
      raise RuntimeError('Received ACK from unconnected resource')
    else:
      self.ACKL.acquire() #We need a lock because += 1 is not atomic
      self.ACKCount += 1
      self.ACKL.release()
      if self.ACKCount == self.ACKCountMax:
        self.ACKEvent.set() #Set the ACK event if all ACKs have been received
    return

#------------------------------------------------------------------------------
class Activator():
  '''
  '''
  #----------------------------------------------------------------------------
  def __init__(self, a, theta, i, f):
    '''
    '''
    assert isinstance(a, int), 'W must be an int'
    assert isinstance(theta, float), 'T must be a float'

    self.ACKL = Lock()
    self.ACKCount = 0
    self.ACKEvent = Event()
    self.ACKCountMax = 0 #should be equal to len(outputList)

    self.dataQueue = Queue()
    self.queueEvent = Event()

    self.outputList = []
    self.inputList = []

    self.a = a
    self.theta = theta #Initial x value
    self.x = theta
    self.c = 0 #Counter

    self.active = False
    return

  #----------------------------------------------------------------------------
  def activate(self):
    '''
    This is the function that will run as a seperate process.  Everything
    else in the class just access data.  Call this function when
    everything is connected and finalized.
    '''
    self.ackCountMax = len(self.outputList)
    self.queueEvent.clear()
    self.ACKEvent.clear()
    self.active = True
    while True:
      self.queueEvent.wait() #Wait until the queue has data
      x, R = self.dataQueue.get() #Get data from the queue
      R.ACK(self) #send an ACK to the resource that sent the data
      self.x = self.i(self.x, x) #Apply iterator
      self.c += 1 #Increment counter 
      if self.c == self.a: #When the counter is full
        self.c = 0 #Reset the counter
        self.x = self.f(self.x) #Apply the activation function
        assert self.ACKCount == 0, 'ACKCount is not 0 prior to outputting!'
        for r in self.outputList:
          r.push(self.x, self) #Send the value to each output connection
          self.x = self.theta #Reset x
          self.c = 0 #Reset the counter
          self.ACKEvent.wait() #Wait for all ACKs
          self.ACKEvent.clear() #Clear the ACK event
          self.ACKCount = 0 #Reset the ACK count
      if self.dataQueue.empty(): #If the dataQueue is empty we must wait
        self.queueEvent.clear()
    return

  #----------------------------------------------------------------------------
  def appendOutput(self, R):
    '''
    Simply appends the resource R to the outputList.  This is mostly for 
    checking for programmer errors, it isn't necessary.  I may remove this
    method in the future.
    '''
    if not isinstance(R, (Link, Activator)):
      raise TypeError('R must be a Link or an Activator')
    self.outputList.append(R)
    return

  #----------------------------------------------------------------------------
  def appendInput(self, R):
    '''
    Simply appends the resource R to the inputList.  This is mostly for 
    checking for programmer errors, it isn't necessary.  I may remove this
    method in the future.
    '''
    if not isinstance(R, (Link, Activator)):
      raise TypeError('R must be a Link or an Activator')
    self.inputList.append(R)
    return

  #----------------------------------------------------------------------------
  def push(self, x, R):
    '''
    The resource R pushes the value x to the Queue.  If R is not in the
    inputList, it is an error.
    '''
    if R not in self.inputList:
      raise RuntimeError('Received task from unconnected resource')
    else:
      self.dataQueue.put((x, R)) #Package into a tuple and put to Queu
      self.queueEvent.set() #Set the queue event
    return

  #----------------------------------------------------------------------------
  def ACK(self, R):
    '''
    The resource R sends an acknowledgement to this Activator.  If R is not
    in the outputList, it is an error.
    '''
    if R not in self.outputList:
      raise RuntimeError('Received ACK from unconnected resource')
    else:
      self.ACKL.acquire() #We need a lock because += 1 is not atomic
      self.ACKCount += 1
      self.ACKL.release()
      if self.ACKCount == self.ACKCountMax:
        self.ACKEvent.set() #Set the ACK event if all ACKs have been received
    return
